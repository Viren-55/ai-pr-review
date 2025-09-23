#!/usr/bin/env python3
"""
Complete integration test for GitHub PR analysis with real Azure OpenAI
"""

import requests
import json
import time

def test_complete_integration():
    """Test the complete flow from frontend to backend with real Azure OpenAI"""
    
    pr_url = "https://github.com/Viren-55/poc-outreach-workflow/pull/1"
    language = "javascript"
    endpoint = "http://127.0.0.1:8000/review/github-pr"
    
    print("=" * 70)
    print("🧪 COMPLETE INTEGRATION TEST - GitHub PR Analysis with Azure OpenAI")
    print("=" * 70)
    print()
    
    print("📍 Configuration:")
    print(f"   PR URL: {pr_url}")
    print(f"   Language: {language}")
    print(f"   Endpoint: {endpoint}")
    print()
    
    payload = {
        "pr_url": pr_url,
        "language": language
    }
    
    try:
        print("🚀 Sending request to backend...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  Response received in {elapsed_time:.2f} seconds")
        print(f"📡 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            # Check overall status
            if data.get("status") == "success":
                print("✅ SUCCESS - Backend API Response Valid")
                print()
                
                # Check if we're in demo mode
                demo_mode = data.get("demo_mode", False)
                print(f"🔧 Mode: {'DEMO' if demo_mode else 'PRODUCTION (Azure OpenAI)'}")
                print()
                
                # Analyze the response structure
                analysis = data.get("analysis", {})
                
                # PR Info
                pr_info = analysis.get("pr_info", {})
                print("📋 GitHub PR Information:")
                print(f"   Title: {pr_info.get('title', 'N/A')}")
                print(f"   Author: {pr_info.get('author', 'N/A')}")
                print(f"   Repository: {pr_info.get('repository', 'N/A')}")
                print(f"   PR Number: {pr_info.get('pr_number', 'N/A')}")
                print(f"   State: {pr_info.get('state', 'N/A')}")
                print()
                
                # Changes Summary
                changes = analysis.get("changes_summary", {})
                print("📊 Changes Summary:")
                print(f"   Files Changed: {changes.get('files_changed', 0)}")
                print(f"   Additions: +{changes.get('additions', 0)}")
                print(f"   Deletions: -{changes.get('deletions', 0)}")
                print(f"   Changed Files: {changes.get('changed_files', [])}")
                print()
                
                # AI Analysis
                ai_analysis = analysis.get("analysis", {})
                print("🤖 AI Analysis Results:")
                print(f"   Overall Score: {ai_analysis.get('overall_score', 'N/A')}/100")
                print(f"   Files Analyzed: {ai_analysis.get('files_analyzed', 0)}")
                print(f"   Total Lines: {ai_analysis.get('total_lines_analyzed', 0)}")
                print(f"   Summary: {ai_analysis.get('analysis_summary', 'N/A')}")
                print()
                
                # Issues Found
                issues = ai_analysis.get('issues', [])
                print(f"🔍 Issues Found: {len(issues)}")
                if issues:
                    for i, issue in enumerate(issues, 1):
                        print(f"\n   Issue #{i}:")
                        print(f"   Title: {issue.get('title', 'Untitled')}")
                        print(f"   Severity: {issue.get('severity', 'unknown').upper()}")
                        print(f"   Category: {issue.get('category', 'General')}")
                        print(f"   File: {issue.get('file_path', 'N/A')}")
                        print(f"   Description: {issue.get('description', 'N/A')}")
                        if issue.get('suggested_fix'):
                            print(f"   Fix: {issue.get('suggested_fix')}")
                else:
                    print("   ✅ No issues found - code is clean!")
                print()
                
                # Metadata
                metadata = analysis.get("metadata", {})
                print("📈 Performance Metrics:")
                print(f"   Analysis Time: {metadata.get('analysis_time_seconds', 'N/A')} seconds")
                print(f"   Analyzed At: {metadata.get('analyzed_at', 'N/A')}")
                print()
                
                # Validate data quality
                print("🔍 Data Validation:")
                validation_checks = [
                    ("PR Title is real", pr_info.get('title') == "Update api_docs.html"),
                    ("Author is correct", pr_info.get('author') == "Viren-55"),
                    ("Repository is correct", pr_info.get('repository') == "Viren-55/poc-outreach-workflow"),
                    ("Not in demo mode", not demo_mode),
                    ("Has real AI analysis", ai_analysis.get('overall_score') is not None),
                    ("File changes detected", changes.get('files_changed', 0) > 0)
                ]
                
                all_valid = True
                for check_name, check_result in validation_checks:
                    status = "✅" if check_result else "❌"
                    print(f"   {status} {check_name}")
                    if not check_result:
                        all_valid = False
                print()
                
                if all_valid:
                    print("🎉 ALL VALIDATION CHECKS PASSED!")
                    print("The system is working correctly with real Azure OpenAI and real GitHub data.")
                else:
                    print("⚠️  Some validation checks failed. Please review the configuration.")
                
                return all_valid
            else:
                print(f"❌ ERROR - API returned non-success status: {data.get('status')}")
                return False
        else:
            print(f"❌ ERROR - HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR - Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR - Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_integration()
    print("\n" + "=" * 70)
    if success:
        print("✅ INTEGRATION TEST PASSED - System is ready for production use!")
    else:
        print("❌ INTEGRATION TEST FAILED - Please check the issues above")
    print("=" * 70)