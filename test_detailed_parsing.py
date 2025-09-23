#!/usr/bin/env python3
"""
Test detailed parsing of AI responses to see line numbers and suggestions
"""

import requests
import json

def test_detailed_parsing():
    """Test if line numbers and suggestions are now being parsed correctly"""
    
    # Simple code with clear line numbers
    test_code = '''def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)  # Line 2: SQL injection
    return execute_query(query)

PASSWORD = "admin123"  # Line 5: Hardcoded password

def divide(a, b):
    return a / b  # Line 8: No zero check'''
    
    print("=" * 70)
    print("🔍 TESTING DETAILED AI RESPONSE PARSING")
    print("=" * 70)
    
    print("📝 Test Code with clear line references:")
    for i, line in enumerate(test_code.split('\n'), 1):
        print(f"{i:2}: {line}")
    
    print("\n🚀 Sending for analysis...")
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/submissions",
            json={
                "code": test_code, 
                "language": "python",
                "submission_type": "paste"
            },
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Analysis complete!")
            print(f"   Submission ID: {data.get('id')}")
            
            # Get the analysis details
            if data.get('analysis'):
                analysis = data['analysis']
                print(f"\n📊 Analysis Results:")
                print(f"   Overall Score: {analysis.get('overall_score', 'N/A')}/100")
                print(f"   Issues Found: {len(analysis.get('issues', []))}")
                
                issues = analysis.get('issues', [])
                print(f"\n🔍 Issue Details:")
                for i, issue in enumerate(issues, 1):
                    print(f"\n   Issue #{i}:")
                    print(f"   ├── Title: {issue.get('title')}")
                    print(f"   ├── Severity: {issue.get('severity', 'N/A').upper()}")
                    print(f"   ├── Category: {issue.get('category', 'N/A')}")
                    print(f"   ├── Line Number: {issue.get('line_number', 'Not detected')}")
                    print(f"   ├── Code Snippet: {issue.get('code_snippet', 'N/A')}")
                    print(f"   ├── Description: {issue.get('description', 'N/A')[:100]}...")
                    print(f"   └── Suggested Fix: {issue.get('suggested_fix', 'No fix available')}")
                
                # Test specific expectations
                print(f"\n✅ Verification:")
                line_numbers_detected = sum(1 for issue in issues if issue.get('line_number'))
                suggestions_provided = sum(1 for issue in issues if issue.get('suggested_fix') and issue.get('suggested_fix') != 'No fix available')
                
                print(f"   ├── Line numbers detected: {line_numbers_detected}/{len(issues)}")
                print(f"   └── Suggestions provided: {suggestions_provided}/{len(issues)}")
                
                return {
                    "issues_found": len(issues),
                    "line_numbers_detected": line_numbers_detected,
                    "suggestions_provided": suggestions_provided
                }
            else:
                print("⚠️  No analysis data found")
                return None
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_detailed_parsing()
    
    print("\n" + "=" * 70)
    if result:
        print("📊 FINAL ASSESSMENT:")
        if result["line_numbers_detected"] > 0:
            print("✅ Line number detection is working!")
        else:
            print("❌ Line numbers still not being detected")
            
        if result["suggestions_provided"] > 0:
            print("✅ AI suggestions are being generated!")
        else:
            print("❌ Suggestions still not being provided")
            
        if result["issues_found"] > 0:
            print("✅ AI is detecting issues correctly")
        else:
            print("❌ No issues detected")
    else:
        print("❌ Test failed - could not get analysis results")
    print("=" * 70)