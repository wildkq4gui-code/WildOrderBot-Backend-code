#!/usr/bin/env python3
"""
Lichess Chess Bot using Stockfish 17.1
Plays at 3000+ level with adaptive time management
"""

import os
import sys
import time
import random
import json
import chess
import chess.engine
import berserk
from typing import Optional, Tuple, Literal, List, Set
from opening_book import get_opening_move
from middlegame_book import get_middlegame_move
from endgame_book import get_endgame_move, is_endgame
from variant_opening_books import get_variant_opening_move


class LichessBot:
    def __init__(self, token: str, stockfish_path: str = "./stockfish/stockfish-ubuntu-x86-64-avx2", blocklist_file: str = "blocklist.json"):
        """Initialize the Lichess bot with API token and Stockfish path."""
        self.token = token
        self.stockfish_path = stockfish_path
        self.fairy_stockfish_path = "./stockfish/fairy-stockfish"
        self.blocklist_file = blocklist_file
        self.session = berserk.TokenSession(token)
        self.client = berserk.Client(session=self.session)
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self.username = None
        self.current_game_id: Optional[str] = None
        self.should_stop = False
        self.blocklist: Set[str] = set()
        self.challenge_accepted = False  # Track if we've accepted a challenge waiting to start
        
        # Scheduling settings
        self.start_time = time.time()
        self.winding_down = False  # True when in wind-down mode (no new challenges)
        self.final_game_played = False  # True after playing the last game
        self.max_runtime_hours = 6.0  # Shutdown after this many hours
        self.winddown_hours = 5.5  # Start wind-down after this many hours
        
        # Engine selection settings
        self.use_fairy_stockfish = False  # False = Stockfish, True = Fairy Stockfish
        
        # Variant mapping from Lichess to Fairy Stockfish UCI format
        self.variant_map = {
            'standard': 'chess',
            'crazyhouse': 'crazyhouse',
            'chess960': 'fischerandom',
            'kingOfTheHill': 'kingofthehill',
            'threeCheck': '3check',
            'antichess': 'antichess',
            'atomic': 'atomic',
            'horde': 'horde',
            'racingKings': 'racingkings'
        }
        
        # Manual speed control settings
        self.manual_mode = False
        self.manual_time_limit = 0.1  # seconds (0.001 to 5.0)
        self.manual_depth = 20  # depth (1 to 50)
        self.manual_threads = 8  # threads (1 to 128)
        self.manual_hash = 2048  # hash in MB (2 to 8192)
        self.manual_overhead = 50  # milliseconds (1 to 500)
        
        # Challenge control settings
        self.can_challenge_bots = True  # Allow challenging bots
        self.can_challenge_users = True  # Allow challenging users
        self.arena_mode = False  # When enabled, don't send/accept any challenges
        
        print("Initializing Lichess Bot...")
        self._verify_bot_account()
        self._initialize_engine()
        self._load_blocklist()
        
    def _verify_bot_account(self):
        """Verify that the account is a bot account."""
        try:
            account = self.client.account.get()
            self.username = account['username']
            print(f"✓ Connected as: {self.username}")
            
            if 'bot' not in account.get('title', '').lower() and not account.get('title'):
                print("\n⚠ Warning: This doesn't appear to be a bot account.")
                print("To use this bot, your account must be upgraded to a bot account.")
                print("Visit: https://lichess.org/api#tag/Bot/operation/botAccountUpgrade")
        except Exception as e:
            print(f"✗ Failed to connect to Lichess: {e}")
            sys.exit(1)
    
    def _initialize_engine(self):
        """Initialize chess engine (Stockfish or Fairy Stockfish)."""
        try:
            engine_path = self.fairy_stockfish_path if self.use_fairy_stockfish else self.stockfish_path
            engine_name = "Fairy Stockfish" if self.use_fairy_stockfish else "Stockfish"
            
            if not os.path.exists(engine_path):
                print(f"✗ {engine_name} not found at: {engine_path}")
                sys.exit(1)
            
            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            info = self.engine.id
            print(f"✓ Engine initialized: {info['name']}")

            # Check engine identity and warn if it does not look like Stockfish 16
            name_lower = info.get('name', '').lower() if isinstance(info.get('name', ''), str) else ''
            version_lower = info.get('version', '').lower() if isinstance(info.get('version', ''), str) else ''
            if 'stockfish' not in name_lower and 'stockfish' not in version_lower:
                print(f"⚠ Warning: Engine does not identify as Stockfish (found: {info}). Continuing, but results may vary.")
            elif '16' not in version_lower and '16' not in name_lower:
                print(f"⚠ Warning: Engine does not appear to be Stockfish 16 (found: {info}). Continuing, but results may vary.")
            
            # Configure engine for high-level play
            self.engine.configure({
                "Threads": min(8, os.cpu_count() or 4),
                "Hash": 2048,
                "Move Overhead": 2,
            })
            print(f"✓ Engine configured with {min(8, os.cpu_count() or 4)} threads, Hash: 2048 MB")
        except Exception as e:
            print(f"✗ Failed to initialize engine: {e}")
            sys.exit(1)
    
    def _load_blocklist(self):
        """Load blocklist from file."""
        try:
            if os.path.exists(self.blocklist_file):
                with open(self.blocklist_file, 'r') as f:
                    data = json.load(f)
                    self.blocklist = set(username.lower() for username in data.get('blocklist', []))
                print(f"✓ Loaded {len(self.blocklist)} blocked users")
            else:
                self.blocklist = set()
                print("✓ No blocklist file found, starting with empty blocklist")
        except Exception as e:
            print(f"⚠ Error loading blocklist: {e}")
            self.blocklist = set()
    
    def _save_blocklist(self):
        """Save blocklist to file."""
        try:
            with open(self.blocklist_file, 'w') as f:
                json.dump({'blocklist': list(self.blocklist)}, f, indent=2)
            print(f"✓ Saved {len(self.blocklist)} blocked users")
        except Exception as e:
            print(f"✗ Error saving blocklist: {e}")
    
    def add_to_blocklist(self, username: str) -> bool:
        """Add a username to the blocklist."""
        username_lower = username.lower()
        if username_lower not in self.blocklist:
            self.blocklist.add(username_lower)
            self._save_blocklist()
            print(f"✓ Added {username} to blocklist")
            return True
        return False
    
    def remove_from_blocklist(self, username: str) -> bool:
        """Remove a username from the blocklist."""
        username_lower = username.lower()
        if username_lower in self.blocklist:
            self.blocklist.remove(username_lower)
            self._save_blocklist()
            print(f"✓ Removed {username} from blocklist")
            return True
        return False
    
    def is_blocked(self, username: str) -> bool:
        """Check if a username is in the blocklist."""
        return username.lower() in self.blocklist
    
    def get_blocklist(self) -> List[str]:
        """Get the current blocklist."""
        return sorted(list(self.blocklist))
    
    def send_chat_message(self, game_id: str, message: str):
        """Send a chat message in the game."""
        try:
            self.client.bots.post_message(game_id, message)
            print(f"💬 Sent chat: {message}")
        except Exception as e:
            print(f"Error sending chat: {e}")
    
    def get_speed_settings(self) -> dict:
        """Get current speed settings."""
        return {
            "manual_mode": self.manual_mode,
            "manual_time_limit": self.manual_time_limit,
            "manual_depth": self.manual_depth,
            "manual_threads": self.manual_threads,
            "manual_hash": self.manual_hash,
            "manual_overhead": self.manual_overhead
        }
    
    def set_speed_settings(self, manual_mode: Optional[bool] = None, time_limit: Optional[float] = None, depth: Optional[int] = None, threads: Optional[int] = None, hash_size: Optional[int] = None, overhead: Optional[int] = None):
        """Update speed settings."""
        if manual_mode is not None:
            self.manual_mode = manual_mode
        if time_limit is not None:
            self.manual_time_limit = max(0.001, min(5.0, time_limit))
        if depth is not None:
            self.manual_depth = max(1, min(50, depth))
        if threads is not None:
            self.manual_threads = max(1, min(128, threads))
        if hash_size is not None:
            self.manual_hash = max(2, min(8192, hash_size))
        if overhead is not None:
            self.manual_overhead = max(1, min(500, overhead))
        
        # Update engine configuration when settings change
        if self.engine:
            config = {}
            
            # Always update overhead
            if manual_mode is not None or overhead is not None:
                effective_overhead = self.manual_overhead if self.manual_mode else 2
                config["Move Overhead"] = effective_overhead
            
            # Update threads and hash if in manual mode or if they're being set
            if self.manual_mode or threads is not None:
                config["Threads"] = self.manual_threads
            
            if self.manual_mode or hash_size is not None:
                config["Hash"] = self.manual_hash
            
            if config:
                self.engine.configure(config)
    
    def get_challenge_settings(self) -> dict:
        """Get current challenge control settings."""
        return {
            "can_challenge_bots": self.can_challenge_bots,
            "can_challenge_users": self.can_challenge_users,
            "arena_mode": self.arena_mode
        }
    
    def set_challenge_settings(self, can_challenge_bots: Optional[bool] = None, can_challenge_users: Optional[bool] = None, arena_mode: Optional[bool] = None):
        """Update challenge control settings."""
        if can_challenge_bots is not None:
            self.can_challenge_bots = can_challenge_bots
        if can_challenge_users is not None:
            self.can_challenge_users = can_challenge_users
        if arena_mode is not None:
            self.arena_mode = arena_mode
    
    @property
    def supported_variants(self) -> Set[str]:
        """Get supported variants based on current engine."""
        if self.use_fairy_stockfish:
            # Fairy Stockfish supports all variants
            return {
                'standard', 'crazyhouse', 'chess960', 'kingOfTheHill', 
                'threeCheck', 'antichess', 'atomic', 'horde', 'racingKings'
            }
        else:
            # Regular Stockfish only supports standard and chess960
            return {'standard', 'chess960'}
    
    def get_engine_settings(self) -> dict:
        """Get current engine settings."""
        return {
            "use_fairy_stockfish": self.use_fairy_stockfish,
            "supported_variants": list(self.supported_variants)
        }
    
    def set_engine_settings(self, use_fairy_stockfish: Optional[bool] = None):
        """Update engine settings and reinitialize if needed."""
        if use_fairy_stockfish is not None and use_fairy_stockfish != self.use_fairy_stockfish:
            # Close existing engine
            if self.engine:
                try:
                    self.engine.quit()
                except:
                    pass
            
            # Update setting and reinitialize
            self.use_fairy_stockfish = use_fairy_stockfish
            self._initialize_engine()
    
    def get_time_limit(self, game_state: dict, bot_is_white: bool, initial: float, increment: float) -> Tuple[float, int]:
        """
        Calculate adaptive time limit based on game time control.
        Optimized for instant and accurate play in 1+0 (60 second) bullet games.
        If manual mode is enabled, uses manual settings instead.
        """
        # Use manual settings if manual mode is enabled
        if self.manual_mode:
            return self.manual_time_limit, self.manual_depth
        
        try:
            wtime = game_state.get('wtime', 0) / 1000
            btime = game_state.get('btime', 0) / 1000
            
            time_left = wtime if bot_is_white else btime
            moves_str = game_state.get('moves', '')
            moves_played = len(moves_str.split()) if moves_str else 0
            
            if initial <= 60 and increment == 0:
                time_limit = min(0.84, time_left * 0.01)
                depth = 30
            elif initial <= 60:
                time_limit = min(0.86, time_left * 0.01)
                depth = 30
            elif initial + increment * 40 <= 180:
                time_limit = min(0.9, time_left * 0.015)
                depth = 45
            elif initial + increment * 40 <= 480:
                time_limit = min(2.0, time_left * 0.03)
                depth = 35
            elif initial + increment * 40 <= 900:
                time_limit = min(5.0, time_left * 0.04)
                depth = 35
            else:
                time_limit = min(15.0, time_left * 0.05)
                depth = 35
            
            if moves_played < 12 and initial <= 60:
                time_limit = max(time_limit * 0.85, 0.82)
            
            time_limit = max(0.82, time_limit)
            
            return time_limit, depth
            
        except Exception as e:
            print(f"Error calculating time limit: {e}")
            return 3.88, 45
    
    def make_move(self, game_id: str, game_state: dict, bot_is_white: bool, initial: float, increment: float, variant: str = 'standard') -> Optional[str]:
        """Calculate and make the best move."""
        if not self.engine:
            print("Error: Engine not initialized")
            return None
            
        try:
            moves = game_state.get('moves', '')
            
            # Create board based on variant
            if variant == 'chess960':
                board = chess.Board(chess960=True)
            elif variant == 'crazyhouse':
                import chess.variant as variant_module
                board = variant_module.CrazyhouseBoard()
            elif variant == 'kingOfTheHill':
                import chess.variant as variant_module
                board = variant_module.KingOfTheHillBoard()
            elif variant == 'threeCheck':
                import chess.variant as variant_module
                board = variant_module.ThreeCheckBoard()
            elif variant == 'antichess':
                import chess.variant as variant_module
                board = variant_module.AntichessBoard()
            elif variant == 'atomic':
                import chess.variant as variant_module
                board = variant_module.AtomicBoard()
            elif variant == 'horde':
                import chess.variant as variant_module
                board = variant_module.HordeBoard()
            elif variant == 'racingKings':
                import chess.variant as variant_module
                board = variant_module.RacingKingsBoard()
            else:  # standard
                board = chess.Board()
            
            # Set variant for Fairy Stockfish
            if self.use_fairy_stockfish and variant in self.variant_map:
                uci_variant = self.variant_map[variant]
                try:
                    self.engine.configure({"UCI_Variant": uci_variant})
                except:
                    pass  # Some options might not be settable
            
            if moves:
                for move_uci in moves.split():
                    board.push_uci(move_uci)
            
            if board.is_game_over():
                return None
            
            # Check chess books
            move_uci = None
            fen = board.fen()
            moves_count = len(moves.split()) if moves else 0
            
            if variant == 'standard':
                # Try opening book first (moves 0-15)
                if moves_count <= 15:
                    book_move = get_opening_move(fen)
                    if book_move and chess.Move.from_uci(book_move) in board.legal_moves:
                        move_uci = book_move
                        print(f"📖 Opening book move: {move_uci}")
                
                # Try middlegame book (moves 10-30)
                if not move_uci and 10 <= moves_count <= 30:
                    book_move = get_middlegame_move(fen, moves_count)
                    if book_move and chess.Move.from_uci(book_move) in board.legal_moves:
                        move_uci = book_move
                        print(f"📖 Middlegame book move: {move_uci}")
                
                # Try endgame book
                if not move_uci and is_endgame(board):
                    book_move = get_endgame_move(fen)
                    if book_move and chess.Move.from_uci(book_move) in board.legal_moves:
                        move_uci = book_move
                        print(f"📖 Endgame book move: {move_uci}")
            else:
                # Try variant-specific opening book (moves 0-10)
                if moves_count <= 10:
                    book_move = get_variant_opening_move(variant, fen)
                    if book_move and chess.Move.from_uci(book_move) in board.legal_moves:
                        move_uci = book_move
                        print(f"📖 {variant.title()} book move: {move_uci}")
            
            # If no book move found, use engine
            if not move_uci:
                time_limit, depth = self.get_time_limit(game_state, bot_is_white, initial, increment)
                
                print(f"Thinking (limit: {time_limit:.2f}s, depth: {depth})...", end=' ', flush=True)
                
                result = self.engine.play(
                    board, 
                    chess.engine.Limit(time=time_limit, depth=depth),
                    info=chess.engine.INFO_ALL
                )
                
                if result.move:
                    move_uci = result.move.uci()
                    score = result.info.get('score', None)
                    score_str = f" (score: {score})" if score else ""
                    print(f"Move: {move_uci}{score_str}")
            
            # Make the move (either from book or engine)
            if move_uci:
                self.client.bots.make_move(game_id, move_uci)
                return move_uci
            
        except Exception as e:
            print(f"Error making move: {e}")
        
        return None
    
    def is_our_turn(self, game_state: dict, bot_is_white: bool) -> bool:
        """Check if it's the bot's turn by reconstructing the board."""
        moves_str = game_state.get('moves', '')
        board = chess.Board()
        
        if moves_str:
            for move_uci in moves_str.split():
                try:
                    board.push_uci(move_uci)
                except ValueError:
                    return False
        
        return (board.turn == chess.WHITE) == bot_is_white
    
    def handle_game(self, game_id: str):
        """Handle a single game."""
        try:
            self.current_game_id = game_id
            print(f"\n{'='*60}")
            print(f"Starting game: {game_id}")
            print(f"{'='*60}")
            
            bot_is_white = None
            initial = 180.0
            increment = 0.0
            chat_sent = False
            variant = 'standard'
            
            for event in self.client.bots.stream_game_state(game_id):
                if event['type'] == 'gameFull':
                    variant = event.get('variant', {}).get('key', 'standard')
                    print(f"Game started: {event['white']['name']} vs {event['black']['name']}")
                    print(f"Variant: {variant}")
                    
                    clock = event.get('clock', {})
                    initial = clock.get('initial', 180000) / 1000
                    increment = clock.get('increment', 0) / 1000
                    
                    print(f"Time control: {initial}s + {increment}s")
                    
                    bot_is_white = event['white'].get('id') == (self.username.lower() if self.username else "")
                    game_state = event['state']
                    
                    if not chat_sent:
                        self.send_chat_message(game_id, "I am WildOrderBot I am almost unstopable!")
                        chat_sent = True
                    
                    if game_state['status'] == 'started' and self.is_our_turn(game_state, bot_is_white):
                        self.make_move(game_id, game_state, bot_is_white, initial, increment, variant)
                
                elif event['type'] == 'gameState':
                    game_state = event
                    
                    if game_state['status'] != 'started':
                        print(f"\nGame finished: {game_state['status']}")
                        break
                    
                    if bot_is_white is None:
                        continue
                    
                    moves = game_state.get('moves', '').split() if game_state.get('moves') else []
                    
                    if len(moves) > 0:
                        print(f"Opponent played: {moves[-1]}")
                    
                    if self.is_our_turn(game_state, bot_is_white):
                        self.make_move(game_id, game_state, bot_is_white, initial, increment, variant)
                
                elif event['type'] == 'chatLine':
                    user = event.get('username', 'Unknown')
                    text = event.get('text', '')
                    print(f"Chat [{user}]: {text}")
            
            self.current_game_id = None
                    
        except Exception as e:
            print(f"Error handling game {game_id}: {e}")
            self.current_game_id = None
    
    def challenge_user(self, username: str, rated: bool = True, clock_limit: int = 180, clock_increment: int = 0):
        """Challenge another user to a game."""
        try:
            if self.current_game_id:
                print(f"✗ Cannot challenge: Already in game {self.current_game_id}")
                return False
            
            if self.arena_mode:
                print(f"✗ Cannot challenge: Arena mode enabled (no challenges allowed)")
                return False
            
            if self.is_blocked(username):
                print(f"✗ Cannot challenge {username}: User is in blocklist")
                return False
            
            # Check if target is a bot
            try:
                user_info = self.client.users.get_public_data(username)
                is_bot = 'BOT' in user_info.get('title', '').upper() or user_info.get('title', '').lower() == 'bot'
                
                if is_bot and not self.can_challenge_bots:
                    print(f"✗ Cannot challenge {username}: Bot challenges disabled")
                    return False
                elif not is_bot and not self.can_challenge_users:
                    print(f"✗ Cannot challenge {username}: User challenges disabled")
                    return False
            except:
                # If we can't determine, assume it's a user
                if not self.can_challenge_users:
                    print(f"✗ Cannot challenge {username}: User challenges disabled")
                    return False
            
            response = self.client.challenges.create(
                username,
                rated=rated,
                clock_limit=clock_limit,
                clock_increment=clock_increment,
                variant='standard'
            )
            print(f"✓ Challenged {username} to a game (rated={rated}, {clock_limit}+{clock_increment})")
            return True
        except Exception as e:
            print(f"✗ Failed to challenge {username}: {e}")
            return False
    
    def accept_challenge(self, challenge_id: str):
        """Accept a game challenge."""
        try:
            if self.arena_mode:
                print(f"  Cannot accept: Arena mode enabled (no challenges allowed)")
                self.decline_challenge(challenge_id, reason="later")
                return
                
            if self.current_game_id:
                print(f"  Cannot accept: Already in game {self.current_game_id}")
                self.decline_challenge(challenge_id, reason="later")
                return
            
            if self.challenge_accepted:
                print(f"  Cannot accept: Already accepted a challenge, waiting for game to start")
                self.decline_challenge(challenge_id, reason="later")
                return
                
            self.client.bots.accept_challenge(challenge_id)
            self.challenge_accepted = True
            print(f"✓ Accepted challenge: {challenge_id}")
        except Exception as e:
            error_msg = str(e)
            if "incompatible with a BOT account" in error_msg:
                print("  Declining: Challenger hasn't enabled playing with bots")
                self.decline_challenge(challenge_id, reason="generic")
            else:
                print(f"✗ Failed to accept challenge: {e}")
    
    def decline_challenge(self, challenge_id: str, reason: Literal['generic', 'later', 'tooFast', 'tooSlow', 'timeControl', 'rated', 'casual', 'standard', 'variant', 'noBot', 'onlyBot'] = "later"):
        """Decline a game challenge."""
        try:
            self.client.bots.decline_challenge(challenge_id, reason=reason)
            print(f"Declined challenge: {challenge_id} ({reason})")
        except Exception as e:
            print(f"Error declining challenge: {e}")
    
    def get_online_bots(self, limit: int = 150) -> List[str]:
        """Get a list of online bot usernames."""
        try:
            online_bots = []
            for bot in self.client.bots.get_online_bots():
                if self.username and bot['username'].lower() != self.username.lower():
                    online_bots.append(bot['username'])
                if len(online_bots) >= limit:
                    break
            return online_bots
        except Exception as e:
            print(f"Error fetching online bots: {e}")
            return []
    
    def challenge_random_bot(self, rated: bool = True, clock_limit: int = 180, clock_increment: int = 0, max_retries: int = 15):
        """Challenge a random online bot to a game with fallback logic.
        
        First tries rated, then casual. If both fail, tries a new bot.
        """
        try:
            if self.current_game_id:
                return False
            
            if self.arena_mode:
                print("✗ Cannot challenge: Arena mode enabled (no challenges allowed)")
                return False
            
            if not self.can_challenge_bots:
                print("✗ Cannot challenge bots: Bot challenges disabled")
                return False
            
            online_bots = self.get_online_bots(limit=80)
            if not online_bots:
                print("No online bots found to challenge")
                return False
            
            # Filter out blocked users
            available_bots = [bot for bot in online_bots if not self.is_blocked(bot)]
            if not available_bots:
                print("No available bots to challenge (all are blocked)")
                return False
            
            bot_to_challenge = random.choice(available_bots)
            
            # Try rated first
            print(f"\n🎯 Challenging random bot: {bot_to_challenge} ({clock_limit}+{clock_increment}, rated)")
            if self.challenge_user(bot_to_challenge, rated=True, clock_limit=clock_limit, clock_increment=clock_increment):
                return True
            
            # If rated fails, try casual
            print("   Rated challenge failed, trying casual...")
            if self.challenge_user(bot_to_challenge, rated=False, clock_limit=clock_limit, clock_increment=clock_increment):
                return True
            
            # If both fail, try a new bot (with retry limit)
            if max_retries > 0:
                print("   Casual challenge also failed, trying a different bot...")
                time.sleep(1)  # Brief delay before retry
                return self.challenge_random_bot(rated=rated, clock_limit=clock_limit, clock_increment=clock_increment, max_retries=max_retries-1)
            else:
                print("   Max retries reached, giving up")
                return False
                
        except Exception as e:
            print(f"Error challenging random bot: {e}")
            return False
    
    def run(self, challenge_users: Optional[List[str]] = None, auto_challenge_bots: bool = True):
        """Main bot loop - listen for events and handle games.
        
        Args:
            challenge_users: Optional list of usernames to challenge at startup
            auto_challenge_bots: If True, automatically challenge random bots when idle
        """
        print(f"\n{'='*60}")
        print("Bot is now running and listening for challenges...")
        if auto_challenge_bots:
            print("Auto-challenging random bots enabled (3+0 blitz)")
        print(f"Schedule: Wind-down at {self.winddown_hours}h, Shutdown at {self.max_runtime_hours}h")
        print(f"{'='*60}\n")
        
        if challenge_users:
            print(f"Challenging users: {', '.join(challenge_users)}")
            for username in challenge_users:
                self.challenge_user(username, rated=True, clock_limit=180, clock_increment=2)
                time.sleep(1)
        elif auto_challenge_bots and not self.winding_down:
            print("Challenging a random bot to start...")
            self.challenge_random_bot(rated=True, clock_limit=180, clock_increment=0)
            time.sleep(2)
        
        try:
            for event in self.client.bots.stream_incoming_events():
                # Check schedule status
                schedule_status = self.check_schedule()
                runtime_hours = self.get_runtime_hours()
                
                if schedule_status == 'shutdown':
                    print(f"\n⏰ Maximum runtime ({self.max_runtime_hours}h) reached after {runtime_hours:.2f}h")
                    print("Shutting down bot...")
                    break
                
                if schedule_status == 'winding_down' and not self.winding_down:
                    self.winding_down = True
                    print(f"\n⏰ Wind-down mode activated at {runtime_hours:.2f}h")
                    print("No new challenges will be accepted. Playing final game...")
                    
                    # If not currently in a game, challenge one last bot
                    if not self.current_game_id and not self.challenge_accepted and auto_challenge_bots:
                        print("Challenging one final bot...")
                        self.challenge_random_bot(rated=False, clock_limit=180, clock_increment=0)
                
                if self.should_stop:
                    print("\nStop signal received, shutting down...")
                    break
                
                # If winding down and no current game and final game was played, exit
                if self.winding_down and not self.current_game_id and self.final_game_played:
                    print("\n✓ Final game completed. Shutting down bot...")
                    break
                
                if event['type'] == 'challenge':
                    challenge = event['challenge']
                    challenger = challenge['challenger']['name']
                    variant = challenge.get('variant', {}).get('key', 'standard, chess960')
                    rated = challenge.get('rated', False)
                    
                    time_control = challenge.get('timeControl', {})
                    if isinstance(time_control, dict):
                        tc_type = time_control.get('type', 'unknown')
                        if tc_type == 'clock':
                            initial = time_control.get('limit', 0)
                            increment = time_control.get('increment', 0)
                            tc_str = f"{initial}+{increment}"
                        else:
                            tc_str = tc_type
                    else:
                        tc_str = 'unknown'
                    
                    print(f"\n→ Challenge from {challenger} ({variant}, {'rated' if rated else 'casual'}, {tc_str})")
                    
                    if self.winding_down:
                        print(f"  Declining: Bot is winding down, not accepting new challenges")
                        self.decline_challenge(challenge['id'], reason="later")
                    elif self.current_game_id:
                        print(f"  Declining: Already playing game {self.current_game_id}")
                        self.decline_challenge(challenge['id'], reason="later")
                    elif self.challenge_accepted:
                        print(f"  Declining: Already accepted a challenge, waiting for game to start")
                        self.decline_challenge(challenge['id'], reason="later")
                    elif self.is_blocked(challenger):
                        print(f"  Declining: {challenger} is blocked")
                        self.decline_challenge(challenge['id'], reason="generic")
                    elif variant in self.supported_variants:
                        # Check if we're using the right engine for this variant
                        if variant != 'standard' and not self.use_fairy_stockfish:
                            print(f"  Declining: {variant} requires Fairy Stockfish (currently using Stockfish)")
                            self.decline_challenge(challenge['id'], reason="variant")
                        else:
                            self.accept_challenge(challenge['id'])
                    else:
                        print(f"  Declining: Variant {variant} not supported")
                        self.decline_challenge(challenge['id'], reason="variant")
                
                elif event['type'] == 'gameStart':
                    game_id = event['game']['id']
                    self.challenge_accepted = False  # Reset flag when game starts
                    if self.current_game_id and self.current_game_id != game_id:
                        print(f"⚠ Warning: Starting new game {game_id} while {self.current_game_id} is active")
                    self.handle_game(game_id)
                
                elif event['type'] == 'gameFinish':
                    game_id = event['game']['id']
                    print(f"\nGame finished: {game_id}")
                    if self.current_game_id == game_id:
                        self.current_game_id = None
                    
                    # Check if this was the final game during wind-down
                    if self.winding_down:
                        self.final_game_played = True
                        runtime = self.get_runtime_hours()
                        print(f"\n✓ Final game completed at {runtime:.2f}h runtime")
                        print("Bot will shut down now...")
                        break
                    
                    if auto_challenge_bots and not self.current_game_id and not self.winding_down:
                        print("\n⏱ Waiting 3 seconds before challenging next bot...")
                        time.sleep(3)
                        if not self.should_stop and not self.winding_down:
                            self.challenge_random_bot(rated=False, clock_limit=180, clock_increment=0)
                    
        except KeyboardInterrupt:
            print("\n\nShutting down bot...")
        except Exception as e:
            print(f"\nError in main loop: {e}")
        finally:
            self.cleanup()
    
    def get_runtime_hours(self) -> float:
        """Get how long the bot has been running in hours."""
        return (time.time() - self.start_time) / 3600
    
    def check_schedule(self) -> str:
        """Check the current schedule status.
        
        Returns:
            'running' - Normal operation
            'winding_down' - Stop accepting challenges, play one last game
            'shutdown' - Time to stop completely
        """
        runtime = self.get_runtime_hours()
        
        if runtime >= self.max_runtime_hours:
            return 'shutdown'
        elif runtime >= self.winddown_hours:
            return 'winding_down'
        else:
            return 'running'
    
    def stop(self):
        """Signal the bot to stop and close the session."""
        self.should_stop = True
        # Close the session to interrupt the event stream
        try:
            session_obj = getattr(self.session, '_session', None)
            if session_obj:
                session_obj.close()
        except:
            pass
    
    def cleanup(self):
        """Clean up resources."""
        if self.engine:
            print("Closing engine...")
            self.engine.quit()
        print("Bot stopped.")


def main():
    """Main entry point."""
    token = os.environ.get('LICHESS_API_TOKEN')
    
    if not token:
        print("=" * 60)
        print("ERROR: LICHESS_API_TOKEN environment variable not set")
        print("=" * 60)
        print("\nTo run this bot, you need:")
        print("1. A Lichess bot account (upgrade at lichess.org)")
        print("2. An API token with bot:play scope")
        print("3. Set the token as an environment variable")
        print("\nThe agent will request your API token next.")
        print("=" * 60)
        sys.exit(1)
    
    bot = LichessBot(token)
    bot.run()


if __name__ == "__main__":
    main()
