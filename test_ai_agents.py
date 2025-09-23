#!/usr/bin/env python3
"""
Test AI agents directly with sample code
"""

import requests
import json

def test_ai_agents():
    """Test the AI agents with sample Python code containing issues"""
    
    # Read the sample code
    with open('test_sample_code.py', 'r') as f:
        code = f.read()
    
    print("=" * 70)
    print("🤖 TESTING AI AGENTS WITH SAMPLE CODE")
    print("=" * 70)
    print()
    
    # Test the review endpoint
    endpoint = "http://127.0.0.1:8000/review"
    
    payload = {
        "code": code,
        "language": "python"
    }
    
    print("📝 Sample Code Stats:")
    print(f"   Lines: {len(code.splitlines())}")
    print(f"   Characters: {len(code)}")
    print()
    
    print("🚀 Sending to AI agents for analysis...")
    print()
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n📊 Response Structure:")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Model Used: {data.get('model_used', 'N/A')}")
            print(f"   Language: {data.get('language', 'N/A')}")
            print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
            
            # Check if we have a review
            review_text = data.get('review', '')
            print("\n🔍 AI Review Content:")
            print("-" * 50)
            print(review_text[:500] if len(review_text) > 500 else review_text)
            if len(review_text) > 500:
                print(f"\n... (truncated, total length: {len(review_text)} chars)")
            print("-" * 50)
            
            # Check for submission_id (indicates it went through the proper flow)
            if data.get('submission_id'):
                print(f"\n✅ Submission ID: {data.get('submission_id')}")
                
                # Try to get more details via the submission endpoint
                submission_id = data.get('submission_id')
                details_response = requests.get(
                    f"http://127.0.0.1:8000/api/submissions/{submission_id}",
                    timeout=30
                )
                
                if details_response.status_code == 200:
                    details = details_response.json()
                    
                    print("\n📋 Submission Details:")
                    print(f"   Created: {details.get('created_at', 'N/A')}")
                    print(f"   Type: {details.get('submission_type', 'N/A')}")
                    
                    if details.get('analysis'):
                        analysis = details['analysis']
                        print("\n🤖 AI Analysis Details:")
                        print(f"   Overall Score: {analysis.get('overall_score', 'N/A')}/100")
                        print(f"   Model: {analysis.get('model_used', 'N/A')}")
                        print(f"   Summary: {analysis.get('analysis_summary', 'N/A')[:200]}...")
                        
                        issues = analysis.get('issues', [])
                        print(f"\n🚨 Issues Found: {len(issues)}")
                        
                        if issues:
                            for i, issue in enumerate(issues[:5], 1):  # Show first 5 issues
                                print(f"\n   Issue #{i}:")
                                print(f"   Title: {issue.get('title', 'N/A')}")
                                print(f"   Severity: {issue.get('severity', 'N/A').upper()}")
                                print(f"   Category: {issue.get('category', 'N/A')}")
                                print(f"   Line: {issue.get('line_number', 'N/A')}")
                                print(f"   Description: {issue.get('description', 'N/A')[:150]}...")
                                if issue.get('suggested_fix'):
                                    print(f"   Fix: {issue.get('suggested_fix', '')[:100]}...")
                            
                            if len(issues) > 5:
                                print(f"\n   ... and {len(issues) - 5} more issues")
                        else:
                            print("   ✅ No issues found!")
            
            return data
        else:
            print(f"\n❌ ERROR - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Testing AI agents with sample code containing multiple issues...")
    print("Expected: SQL injection, hardcoded credentials, performance issues, etc.")
    print()
    
    result = test_ai_agents()
    
    print("\n" + "=" * 70)
    if result and result.get('status') == 'success':
        print("✅ AI Agents responded successfully")
        
        # Check if we got real analysis
        review = result.get('review', '')
        if 'SQL' in review or 'injection' in review or 'security' in review.lower():
            print("✅ AI detected security issues")
        else:
            print("⚠️  AI may not have detected the SQL injection vulnerability")
            
        if 'password' in review.lower() or 'credentials' in review.lower() or 'API_KEY' in review:
            print("✅ AI detected hardcoded credentials")
        else:
            print("⚠️  AI may not have detected hardcoded credentials")
            
        if 'fibonacci' in review or 'recursion' in review or 'memoization' in review:
            print("✅ AI detected performance issues")
        else:
            print("⚠️  AI may not have detected recursion performance issue")
    else:
        print("❌ AI Agents failed to analyze the code")
    print("=" * 70)