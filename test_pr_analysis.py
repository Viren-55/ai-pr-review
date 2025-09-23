#!/usr/bin/env python3
"""
Simple test script to verify GitHub PR analysis with real Azure OpenAI credentials
"""

import requests
import json
import sys

def test_pr_analysis():
    """Test the PR analysis endpoint with real data"""
    
    # Test data
    pr_url = "https://github.com/Viren-55/poc-outreach-workflow/pull/1"
    language = "javascript"
    
    # Backend endpoint
    endpoint = "http://127.0.0.1:8000/review/github-pr"
    
    print("🔍 Testing GitHub PR Analysis with Azure OpenAI")
    print(f"📍 PR URL: {pr_url}")
    print(f"🌐 Endpoint: {endpoint}")
    print("-" * 60)
    
    # Make the request
    payload = {
        "pr_url": pr_url,
        "language": language
    }
    
    try:
        print("🚀 Sending request...")
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we're in demo mode or production
            demo_mode = data.get("demo_mode", False)
            print(f"🎯 Demo Mode: {'Yes' if demo_mode else 'No (Production)'}")
            
            if data.get("status") == "success":
                analysis = data.get("analysis", {})
                pr_info = analysis.get("pr_info", {})
                changes_summary = analysis.get("changes_summary", {})
                ai_analysis = analysis.get("analysis", {})
                
                print("\n✅ SUCCESS - Real GitHub Data Retrieved:")
                print(f"   📝 Title: {pr_info.get('title', 'N/A')}")
                print(f"   👤 Author: {pr_info.get('author', 'N/A')}")
                print(f"   📂 Repository: {pr_info.get('repository', 'N/A')}")
                print(f"   🔢 PR Number: {pr_info.get('pr_number', 'N/A')}")
                print(f"   📊 State: {pr_info.get('state', 'N/A')}")
                print(f"   📁 Files Changed: {changes_summary.get('files_changed', 'N/A')}")
                print(f"   ➕ Additions: {changes_summary.get('additions', 'N/A')}")
                print(f"   ➖ Deletions: {changes_summary.get('deletions', 'N/A')}")
                print(f"   📋 Changed Files: {changes_summary.get('changed_files', [])}")
                
                print(f"\n🤖 AI Analysis Results:")
                print(f"   📊 Overall Score: {ai_analysis.get('overall_score', 'N/A')}/100")
                print(f"   🔍 Issues Found: {len(ai_analysis.get('issues', []))}")
                print(f"   📝 Summary: {ai_analysis.get('analysis_summary', 'N/A')}")
                
                # Show issues if any
                issues = ai_analysis.get('issues', [])
                if issues:
                    print(f"\n🚨 Issues Details:")
                    for i, issue in enumerate(issues, 1):
                        print(f"   {i}. {issue.get('title', 'Untitled')} ({issue.get('severity', 'unknown').upper()})")
                        print(f"      📁 File: {issue.get('file_path', 'N/A')}")
                        print(f"      📝 Description: {issue.get('description', 'N/A')}")
                        if issue.get('suggested_fix'):
                            print(f"      🔧 Fix: {issue.get('suggested_fix', 'N/A')}")
                        print()
                
                # Metadata
                metadata = analysis.get("metadata", {})
                print(f"📊 Analysis Metadata:")
                print(f"   ⏱️  Analysis Time: {metadata.get('analysis_time_seconds', 'N/A')} seconds")
                print(f"   🗓️  Analyzed At: {metadata.get('analyzed_at', 'N/A')}")
                print(f"   💾 Language: {metadata.get('language', 'N/A')}")
                
                print(f"\n🎉 Test PASSED - PR analysis working with real Azure OpenAI!")
                return True
            else:
                print(f"❌ ERROR - Response status not success: {data}")
                return False
        else:
            print(f"❌ ERROR - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
            except:
                print(f"   Error Text: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR - Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ ERROR - Invalid JSON response: {e}")
        print(f"   Response: {response.text}")
        return False
    except Exception as e:
        print(f"❌ ERROR - Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_pr_analysis()
    sys.exit(0 if success else 1)