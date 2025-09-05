#!/usr/bin/env python3
"""
Test script to debug token detection issues
"""
import os
import sys

def test_token_detection():
    print("=== Token Detection Debug ===")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Test different ways to get the token
    methods = [
        ("os.getenv('GITHUB_TOKEN')", os.getenv('GITHUB_TOKEN')),
        ("os.environ.get('GITHUB_TOKEN')", os.environ.get('GITHUB_TOKEN')),
        ("os.getenv('GITHUB_TOKEN', 'DEFAULT')", os.getenv('GITHUB_TOKEN', 'DEFAULT')),
    ]
    
    for method_name, result in methods:
        print(f"{method_name}: {repr(result)}")
    
    # Show all environment variables with 'TOKEN' or 'GITHUB'
    print("\nAll environment variables containing 'TOKEN' or 'GITHUB':")
    for k, v in os.environ.items():
        if 'TOKEN' in k.upper() or 'GITHUB' in k.upper():
            # Mask the token for security
            display_value = v[:10] + "..." if len(v) > 10 else v
            print(f"  {k}: {display_value}")
    
    # Test the BatchHunter initialization logic
    print("\n=== BatchHunter Token Logic Test ===")
    
    # Simulate the BatchHunter.__init__ logic
    token_param = None  # No token passed as parameter
    detected_token = token_param or os.getenv('GITHUB_TOKEN')
    
    print(f"Token parameter: {repr(token_param)}")
    print(f"Detected token: {repr(detected_token)}")
    print(f"Token is truthy: {bool(detected_token)}")
    
    return detected_token

if __name__ == "__main__":
    detected = test_token_detection()
    if detected:
        print(f"\n✅ Token detected successfully: {detected[:10]}...")
    else:
        print(f"\n❌ No token detected")
        print("💡 Try: export GITHUB_TOKEN=your_token_here")
        print("💡 Or pass token directly: --token your_token_here")