#!/usr/bin/env python3
"""Test script for the Code Review API."""

import requests
import json

API_BASE = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_review():
    """Test the review endpoint."""
    print("\nTesting /review endpoint...")
    
    test_code = """def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Example usage
result = calculate_average([1, 2, 3, 4, 5])
print(result)"""
    
    payload = {
        "code": test_code,
        "language": "python"
    }
    
    try:
        response = requests.post(f"{API_BASE}/review", json=payload)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Review completed successfully!")
            print(f"Language: {data.get('language')}")
            print(f"Model used: {data.get('model_used')}")
            print(f"Review length: {len(data.get('review', ''))}")
            print(f"First 200 chars of review: {data.get('review', '')[:200]}...")
            return True
        else:
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_languages():
    """Test the languages endpoint."""
    print("\nTesting /languages endpoint...")
    try:
        response = requests.get(f"{API_BASE}/languages")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Supported languages: {len(data.get('languages', []))}")
            for lang in data.get('languages', [])[:3]:  # Show first 3
                print(f"  - {lang.get('name')}: {lang.get('value')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Code Review API Integration")
    print("=" * 50)
    
    health_ok = test_health()
    languages_ok = test_languages()
    review_ok = test_review()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Health check: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Languages endpoint: {'✅ PASS' if languages_ok else '❌ FAIL'}")
    print(f"Review endpoint: {'✅ PASS' if review_ok else '❌ FAIL'}")
    
    if all([health_ok, languages_ok, review_ok]):
        print("\n🎉 All tests passed! API is working correctly.")
        print("Frontend should now be able to connect successfully.")
    else:
        print("\n⚠️ Some tests failed. Check the backend service.")