"""Test complete flow: Code Submission → Analysis → Insights → Auto-fixes"""

import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents_v2.orchestrator import AgentOrchestrator
from agents_v2.models import CodeContext

# Load environment variables
load_dotenv()


async def test_full_flow():
    """Test complete flow from submission to auto-fixes."""
    
    print("\n" + "="*80)
    print(" "*20 + "FULL FLOW TEST: SUBMISSION → ANALYSIS → FIXES")
    print("="*80)
    
    # Sample code with multiple issues
    test_code = '''
def getUserData(username):
    """Get user data from database."""
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    # Hardcoded credentials (security issue)
    api_key = "sk-1234567890abcdefghijklmnop"
    password = "MySecretPassword123"
    
    # Inefficient loop (performance issue)
    for i in range(len(result)):
        print(result[i])
    
    # Reading entire file into memory (performance issue)
    with open('data.txt') as f:
        data = f.read()
    
    # Poor naming convention (camelCase function - quality issue)
    return result

def processUserOrders(userId):
    """Process orders for a user."""
    # Another SQL injection
    query = "SELECT * FROM orders WHERE user_id = " + str(userId)
    return execute_query(query)
'''
    
    print(f"\n📝 Test Code ({len(test_code)} chars, {len(test_code.splitlines())} lines)")
    print("-" * 80)
    print(test_code)
    print("-" * 80)
    
    # Step 1: Initialize Orchestrator
    print("\n" + "="*80)
    print("STEP 1: Initialize AI Agent Orchestrator")
    print("="*80)
    
    azure_client = AzureOpenAI(
        api_key=os.getenv("REASONING_AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("REASONING_AZURE_API_VERSION"),
        azure_endpoint=os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
    )
    model_name = os.getenv("REASONING_MODEL")
    
    print(f"✅ Azure OpenAI client initialized")
    print(f"   Endpoint: {azure_client.base_url}")
    print(f"   Model: {model_name}")
    
    orchestrator = AgentOrchestrator(azure_client=azure_client, model_name=model_name)
    print(f"\n✅ Orchestrator initialized with {len(orchestrator.agents)} agents:")
    for key, agent in orchestrator.agents.items():
        print(f"   - {agent.name}")
    
    # Step 2: Code Submission & Analysis
    print("\n" + "="*80)
    print("STEP 2: Code Submission & Analysis")
    print("="*80)
    
    context = CodeContext(
        code=test_code,
        language="python",
        file_path="user_service.py"
    )
    
    print(f"\n🔍 Starting analysis...")
    print(f"   Language: {context.language}")
    print(f"   File: {context.file_path}")
    
    # Run analysis without recommendations first
    result = await orchestrator.analyze_code(context, include_recommendations=False)
    
    print(f"\n✅ Analysis Complete!")
    print(f"   Total time: {result.analysis_time_seconds:.2f}s")
    print(f"   Overall score: {result.overall_score}/100")
    print(f"   Issues found: {len(result.issues)}")
    print(f"   Summary: {result.summary}")
    
    # Step 3: Display Issues by Category
    print("\n" + "="*80)
    print("STEP 3: Issues Breakdown by Category")
    print("="*80)
    
    # Group issues by category
    issues_by_category = {}
    issues_by_severity = {}
    
    for issue in result.issues:
        category = issue.category.value
        severity = issue.severity.value
        
        if category not in issues_by_category:
            issues_by_category[category] = []
        issues_by_category[category].append(issue)
        
        if severity not in issues_by_severity:
            issues_by_severity[severity] = []
        issues_by_severity[severity].append(issue)
    
    # Display by severity
    print("\n📊 Issues by Severity:")
    severity_order = ['critical', 'high', 'medium', 'low', 'info']
    for severity in severity_order:
        if severity in issues_by_severity:
            count = len(issues_by_severity[severity])
            print(f"   {severity.upper()}: {count} issues")
    
    # Display by category
    print("\n📊 Issues by Category:")
    for category, issues in issues_by_category.items():
        print(f"\n   {category.upper().replace('_', ' ')} ({len(issues)} issues):")
        for i, issue in enumerate(issues[:5], 1):  # Show max 5 per category
            location = f"Line {issue.location.line_start}" if hasattr(issue, 'location') and issue.location else "N/A"
            print(f"      {i}. [{issue.severity.value.upper()}] {issue.title}")
            print(f"         {location} - {issue.description[:80]}...")
        
        if len(issues) > 5:
            print(f"      ... and {len(issues) - 5} more issues")
    
    # Step 4: Generate Auto-Fix Recommendations
    print("\n" + "="*80)
    print("STEP 4: Generate Auto-Fix Recommendations")
    print("="*80)
    
    print(f"\n🔧 Generating fixes for {len(result.issues)} issues...")
    
    # Re-run with recommendations
    result_with_fixes = await orchestrator.analyze_code(context, include_recommendations=True)
    
    recommendations = result_with_fixes.recommendations
    print(f"\n✅ Generated {len(recommendations)} recommendations")
    
    # Display recommendations
    if recommendations:
        print(f"\n📋 Auto-Fix Recommendations:")
        
        # Group by auto-fixable
        auto_fixable = [r for r in recommendations if r.auto_fixable]
        manual_review = [r for r in recommendations if not r.auto_fixable]
        
        print(f"\n   ✅ Auto-fixable: {len(auto_fixable)}")
        print(f"   ⚠️  Requires review: {len(manual_review)}")
        
        # Show top auto-fixable recommendations
        print(f"\n   Top Auto-fixable Recommendations:")
        for i, rec in enumerate(auto_fixable[:5], 1):
            print(f"\n      {i}. {rec.title}")
            print(f"         Confidence: {rec.confidence:.0%}")
            print(f"         Impact: {rec.impact}")
            print(f"         Original: {rec.original_code[:60]}...")
            print(f"         Fixed:    {rec.suggested_code[:60]}...")
    
    # Step 5: Apply Auto-Fixes
    print("\n" + "="*80)
    print("STEP 5: Apply Auto-Fixes")
    print("="*80)
    
    if recommendations:
        # Filter high-confidence auto-fixable recommendations
        high_confidence_fixes = [
            r for r in recommendations 
            if r.auto_fixable and r.confidence >= 0.7
        ]
        
        print(f"\n🔧 Applying {len(high_confidence_fixes)} high-confidence auto-fixes...")
        
        # Create editing session and apply fixes
        session_id = await orchestrator.create_editing_session(context)
        print(f"   Created editing session: {session_id}")
        
        apply_result = await orchestrator.apply_recommendations(
            context, 
            high_confidence_fixes,
            session_id=session_id
        )
        
        print(f"\n✅ Auto-fix Results:")
        print(f"   Total recommendations: {apply_result['total_recommendations']}")
        print(f"   Successfully applied: {apply_result['applied_count']}")
        print(f"   Failed: {apply_result['failed_count']}")
        
        # Show final code if available
        if apply_result.get('final_code'):
            print(f"\n📄 Fixed Code Preview:")
            print("-" * 80)
            lines = apply_result['final_code'].split('\n')
            for i, line in enumerate(lines[:20], 1):  # Show first 20 lines
                print(f"{i:3d} | {line}")
            if len(lines) > 20:
                print(f"... and {len(lines) - 20} more lines")
            print("-" * 80)
        
        # Show diff if available
        if apply_result.get('diff'):
            print(f"\n📊 Changes Summary:")
            diff_data = apply_result['diff']
            if isinstance(diff_data, dict):
                print(f"   Lines changed: {diff_data.get('changes', 'N/A')}")
                print(f"   Session status: {diff_data.get('status', 'N/A')}")
    else:
        print("   No auto-fix recommendations generated")
    
    # Step 6: Final Summary
    print("\n" + "="*80)
    print("STEP 6: Final Summary")
    print("="*80)
    
    print(f"\n📈 Analysis Results:")
    print(f"   Original Code Score: {result.overall_score}/100")
    print(f"   Total Issues Found: {len(result.issues)}")
    print(f"   - Critical: {len(issues_by_severity.get('critical', []))}")
    print(f"   - High: {len(issues_by_severity.get('high', []))}")
    print(f"   - Medium: {len(issues_by_severity.get('medium', []))}")
    print(f"   - Low: {len(issues_by_severity.get('low', []))}")
    
    print(f"\n🔧 Auto-Fix Results:")
    if recommendations:
        print(f"   Recommendations Generated: {len(recommendations)}")
        print(f"   Auto-fixable: {len([r for r in recommendations if r.auto_fixable])}")
        if 'apply_result' in locals():
            print(f"   Successfully Applied: {apply_result['applied_count']}")
    else:
        print(f"   No recommendations generated")
    
    print(f"\n⏱️  Performance:")
    print(f"   Analysis Time: {result.analysis_time_seconds:.2f}s")
    print(f"   Agents Used: {', '.join(result.analyzed_by)}")
    
    print("\n" + "="*80)
    print(" "*25 + "✅ FULL FLOW TEST COMPLETED")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_full_flow())