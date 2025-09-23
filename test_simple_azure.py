#!/usr/bin/env python3
"""
Test simple Azure OpenAI call via backend
"""

import requests
import json

def test_simple_azure_call():
    """Create a simple endpoint test for Azure OpenAI"""
    
    print("=" * 50)
    print("🔌 Testing Simple Azure OpenAI Call")
    print("=" * 50)
    
    # Let's test with a very simple code review request
    simple_code = """
def hello():
    print("Hello World")
"""
    
    endpoint = "http://127.0.0.1:8000/review"
    payload = {
        "code": simple_code,
        "language": "python"
    }
    
    print("📝 Testing with simple code:")
    print(simple_code)
    print("🚀 Sending request...")
    
    try:
        # Use a longer timeout but monitor progress
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes
        )
        
        print(f"✅ Response received! Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Response data:")
            print(f"   Status: {data.get('status')}")
            print(f"   Model: {data.get('model_used')}")
            print(f"   Language: {data.get('language')}")
            
            review = data.get('review', '')
            print(f"\n📝 Review (first 200 chars):")
            print(f"   {review[:200]}...")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 2 minutes")
        print("This suggests the AI agents are hanging or taking too long")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing if Azure OpenAI connection works for simple code review...")
    success = test_simple_azure_call()
    
    if success:
        print("\n✅ Azure OpenAI is working through the backend!")
    else:
        print("\n❌ There's an issue with the Azure OpenAI integration in the backend")