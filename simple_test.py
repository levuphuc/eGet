#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sys

def test_simple_scrape():
    print("🧪 Testing simple scrape...")
    
    # Test với payload đơn giản nhất
    payload = {
        'url': 'https://httpbin.org/html',
        'formats': ['markdown'],
        'onlyMainContent': True,
        'timeout': 30
    }
    
    try:
        print("Sending request...")
        response = requests.post('http://localhost:8000/api/v1/scrape', json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            if result.get('success'):
                markdown = result.get('data', {}).get('markdown', '')
                print(f"Markdown length: {len(markdown)} characters")
                print("✅ SIMPLE TEST PASSED")
                return True
            else:
                error = result.get('data', {}).get('metadata', {}).get('error', 'Unknown')
                print(f"❌ FAILED: {error[:200]}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT after 60 seconds")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

def test_tuesy_minimal():
    print("\n🧪 Testing tuesy.net with minimal config...")
    
    # Test với tuesy.net nhưng config minimal
    payload = {
        'url': 'https://tuesy.net/phat-day-chan-trau/',
        'formats': ['markdown'],
        'onlyMainContent': True,
        'timeout': 60,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }
    
    try:
        print("Sending request...")
        response = requests.post('http://localhost:8000/api/v1/scrape', json=payload, timeout=90)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success', False)}")
            if result.get('success'):
                markdown = result.get('data', {}).get('markdown', '')
                print(f"Markdown length: {len(markdown)} characters")
                print("✅ TUESY TEST PASSED")
                return True
            else:
                error = result.get('data', {}).get('metadata', {}).get('error', 'Unknown')
                print(f"❌ FAILED: {error[:200]}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT after 90 seconds")
        return False
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("SIMPLE DEBUGGING TEST")
    print("=" * 50)
    
    # Test 1: Simple httpbin
    success1 = test_simple_scrape()
    
    # Test 2: Tuesy minimal (chỉ nếu test 1 thành công)
    if success1:
        success2 = test_tuesy_minimal()
        if success2:
            print("\n🎉 All tests passed! Chrome driver is working properly.")
        else:
            print("\n⚠️  Simple test passed but tuesy.net failed - might be site-specific issue.")
    else:
        print("\n❌ Basic test failed - Chrome driver still has issues.")
    
    print("=" * 50)