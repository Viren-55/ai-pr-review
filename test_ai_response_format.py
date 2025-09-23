#!/usr/bin/env python3
"""
Test what format Azure OpenAI is actually returning
"""

import requests
import json

def test_ai_response_format():
    """Test a simple code review to see the actual AI response format"""
    
    # Simple code with obvious issues
    test_code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)  # Line 3: SQL injection
    return execute_query(query)

PASSWORD = "admin123"  # Line 6: Hardcoded password

def divide(a, b):
    return a / b  # Line 9: No zero check
'''
    
    print("=" * 60)
    print("🔍 TESTING AI RESPONSE FORMAT")
    print("=" * 60)
    
    print("📝 Test Code:")
    print(test_code)
    print("\n🚀 Sending to backend...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/review",
            json={"code": test_code, "language": "python"},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Response received!")
            print(f"   Status: {data.get('status')}")
            print(f"   Model: {data.get('model_used')}")
            
            # Get the raw review text
            review_text = data.get('review', '')
            print(f"\n📄 Raw AI Review Text (first 500 chars):")
            print("-" * 50)
            print(review_text[:500])
            print("-" * 50)
            
            # Check if it looks like JSON anywhere
            if '[' in review_text and '{' in review_text:
                print("\n🔍 Possible JSON structure detected")
                # Try to find JSON-like content
                start_idx = review_text.find('[')
                end_idx = review_text.rfind(']') + 1
                if start_idx != -1 and end_idx > start_idx:
                    potential_json = review_text[start_idx:end_idx]
                    print(f"📊 Potential JSON content:")
                    print(potential_json[:300] + "..." if len(potential_json) > 300 else potential_json)
            else:
                print("\n⚠️  No JSON structure detected - AI returning natural language")
                
            # Check what issues were parsed
            if hasattr(data, 'submission_id'):
                print(f"\n📋 Submission ID: {data.get('submission_id')}")
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_response_format()