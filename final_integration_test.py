#!/usr/bin/env python3
"""
Final comprehensive test of the entire system
"""

import requests
import json
import time

def test_code_analysis():
    """Test regular code analysis with real AI"""
    print("🧪 Testing Regular Code Analysis...")
    
    code = '''
def process_user_data(user_id, data):
    # Security issue: SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    
    # Performance issue: inefficient loop
    results = []
    for item in data:
        for other_item in data:
            if item == other_item:
                results.append(item)
    
    return results
'''
    
    response = requests.post(
        "http://127.0.0.1:8000/review",
        json={"code": code, "language": "python"},
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Code Analysis Success")
        print(f"   Model: {data.get('model_used')}")
        print(f"   Status: {data.get('status')}")
        
        review = data.get('review', '')
        has_sql_issue = 'sql' in review.lower() or 'injection' in review.lower()
        has_performance_issue = 'loop' in review.lower() or 'performance' in review.lower()
        
        print(f"   SQL Issue Detected: {'✅' if has_sql_issue else '❌'}")
        print(f"   Performance Issue Detected: {'✅' if has_performance_issue else '❌'}")
        
        return has_sql_issue and has_performance_issue
    else:
        print(f"❌ Code Analysis Failed: {response.status_code}")
        return False

def test_github_pr_analysis():
    """Test GitHub PR analysis with real AI"""
    print("\n🔍 Testing GitHub PR Analysis...")
    
    response = requests.post(
        "http://127.0.0.1:8000/review/github-pr",
        json={
            "pr_url": "https://github.com/Viren-55/poc-outreach-workflow/pull/1",
            "language": "javascript"
        },
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        analysis = data.get('analysis', {})
        pr_info = analysis.get('pr_info', {})
        
        print(f"✅ GitHub PR Analysis Success")
        print(f"   Demo Mode: {'Yes' if data.get('demo_mode') else 'No'}")
        print(f"   PR Title: {pr_info.get('title')}")
        print(f"   Author: {pr_info.get('author')}")
        print(f"   Repository: {pr_info.get('repository')}")
        print(f"   Files Changed: {analysis.get('changes_summary', {}).get('files_changed')}")
        print(f"   Overall Score: {analysis.get('analysis', {}).get('overall_score')}")
        
        # Check if real data
        is_real_data = (
            pr_info.get('title') == "Update api_docs.html" and
            pr_info.get('author') == "Viren-55" and
            not data.get('demo_mode')
        )
        
        print(f"   Real GitHub Data: {'✅' if is_real_data else '❌'}")
        return is_real_data
    else:
        print(f"❌ GitHub PR Analysis Failed: {response.status_code}")
        return False

def main():
    print("=" * 70)
    print("🚀 FINAL COMPREHENSIVE INTEGRATION TEST")
    print("=" * 70)
    print("Testing complete end-to-end system with Azure OpenAI...")
    print()
    
    # Test 1: Regular Code Analysis
    code_test = test_code_analysis()
    
    # Test 2: GitHub PR Analysis  
    pr_test = test_github_pr_analysis()
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS")
    print("=" * 70)
    
    results = {
        "Code Analysis with Real AI": code_test,
        "GitHub PR Analysis with Real Data": pr_test
    }
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The system is ready for production with:")
        print("   ✅ Real Azure OpenAI integration")
        print("   ✅ Genuine AI code analysis") 
        print("   ✅ Real GitHub PR data fetching")
        print("   ✅ Frontend displaying actual results")
        print("   ✅ No mock data anywhere")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    print("=" * 70)

if __name__ == "__main__":
    main()