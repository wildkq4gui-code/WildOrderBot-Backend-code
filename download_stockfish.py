#!/usr/bin/env python3
"""
Download Stockfish binaries for the Lichess bot.
Supports Stockfish 18 (preferred) and 17.1 (fallback).
"""

import os
import sys
import urllib.request
import tarfile
import shutil
from pathlib import Path
from argparse import ArgumentParser


RELEASES = {
    "18": "https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-ubuntu-x86-64-avx2.tar",
    "17.1": "https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar",
}

STOCKFISH_DIR = Path(__file__).parent / "LichessStockfishand-fairy-fish-1" / "stockfish"


def download_stockfish(version):
    """Download and extract a specific Stockfish version."""
    if version not in RELEASES:
        print(f"❌ Unknown version: {version}")
        print(f"Available versions: {', '.join(RELEASES.keys())}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Downloading Stockfish {version}...")
    print(f"{'='*60}")
    
    url = RELEASES[version]
    tar_file = STOCKFISH_DIR / f"stockfish-{version}.tar"
    temp_extract_dir = STOCKFISH_DIR / f"temp_extract_{version.replace('.', '_')}"
    binary_path = STOCKFISH_DIR / f"stockfish-{version}"
    
    try:
        # Create directory if needed
        STOCKFISH_DIR.mkdir(parents=True, exist_ok=True)
        temp_extract_dir.mkdir(exist_ok=True)
        
        # Check if already exists
        if binary_path.exists():
            print(f"✓ Stockfish {version} already exists at {binary_path.name}")
            size_mb = binary_path.stat().st_size / (1024*1024)
            print(f"  Size: {size_mb:.1f} MB")
            return True
        
        # Download
        print(f"Downloading from GitHub...")
        urllib.request.urlretrieve(url, tar_file)
        size_mb = tar_file.stat().st_size / (1024*1024)
        print(f"✓ Downloaded ({size_mb:.1f} MB)")
        
        # Extract
        print(f"Extracting...")
        with tarfile.open(tar_file, 'r') as tar:
            tar.extractall(temp_extract_dir)
        print(f"✓ Extracted")
        
        # Move binary to correct location
        extracted_binary = temp_extract_dir / "stockfish" / "stockfish-ubuntu-x86-64-avx2"
        if extracted_binary.exists():
            shutil.move(str(extracted_binary), str(binary_path))
            print(f"✓ Moved to {binary_path.name}")
        else:
            print(f"❌ Binary not found in extraction")
            return False
        
        # Make executable
        os.chmod(binary_path, 0o755)
        print(f"✓ Made executable")
        
        # Cleanup
        shutil.rmtree(temp_extract_dir)
        tar_file.unlink()
        
        # Verify
        if binary_path.exists() and os.access(binary_path, os.X_OK):
            size_mb = binary_path.stat().st_size / (1024*1024)
            print(f"✓ Stockfish {version} ready! ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ Failed to verify binary")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        # Cleanup on error
        if tar_file.exists():
            tar_file.unlink()
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        return False


def main():
    parser = ArgumentParser(description="Download Stockfish binaries for the bot")
    parser.add_argument(
        "version",
        nargs="?",
        default="18",
        help="Stockfish version to download (18 or 17.1). Default: 18"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available versions"
    )
    
    args = parser.parse_args()
    
    if args.all:
        print("Downloading all Stockfish versions...")
        results = {}
        for version in sorted(RELEASES.keys(), key=lambda v: float(v)):
            results[version] = download_stockfish(version)
        
        print(f"\n{'='*60}")
        print("Summary:")
        print(f"{'='*60}")
        for version, success in results.items():
            status = "✓" if success else "❌"
            print(f"{status} Stockfish {version}")
    else:
        success = download_stockfish(args.version)
        sys.exit(0 if success else 1)
    
    # List available binaries
    print(f"\n{'='*60}")
    print("Available Stockfish binaries:")
    print(f"{'='*60}")
    found_any = False
    for item in sorted(STOCKFISH_DIR.glob("stockfish-*")):
        if item.is_file() and os.access(item, os.X_OK):
            size_mb = item.stat().st_size / (1024*1024)
            print(f"✓ {item.name} ({size_mb:.1f} MB)")
            found_any = True
    
    if not found_any:
        print("No binaries found. Run this script to download one.")


if __name__ == "__main__":
    main()
