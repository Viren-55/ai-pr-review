"""Simple test of the complete analysis flow."""

import asyncio
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents_v2.orchestrator import AgentOrchestrator
from agents_v2.models import CodeContext

# Load environment variables
load_dotenv()


async def test_analysis_flow():
    """Test the analysis flow from code submission to insights."""
    
    print("\n" + "="*80)
    print(" "*15 + "CODE REVIEW FLOW TEST: SUBMISSION → ANALYSIS → INSIGHTS")
    print("="*80)
    
    # Test code with various issues
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
    
    print(f"\n📝 Submitted Code:")
    print(f"   Size: {len(test_code)} chars")
    print(f"   Lines: {len(test_code.splitlines())}")
    print(f"   Language: Python")
    
    # Initialize orchestrator
    print(f"\n⚙️  Initializing AI Agent Orchestrator...")
    
    azure_client = AzureOpenAI(
        api_key=os.getenv("REASONING_AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("REASONING_AZURE_API_VERSION"),
        azure_endpoint=os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
    )
    model_name = os.getenv("REASONING_MODEL")
    
    orchestrator = AgentOrchestrator(azure_client=azure_client, model_name=model_name)
    print(f"✅ Orchestrator initialized with {len(orchestrator.agents)} AI agents")
    
    # Create context and run analysis
    print(f"\n🔍 Running Code Analysis...")
    
    context = CodeContext(
        code=test_code,
        language="python",
        file_path="user_service.py"
    )
    
    result = await orchestrator.analyze_code(context, include_recommendations=False)
    
    # Display results
    print(f"\n✅ Analysis Complete in {result.analysis_time_seconds:.2f}s")
    print(f"\n{'='*80}")
    print("ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    print(f"\n📊 Overall Score: {result.overall_score}/100")
    print(f"\n📝 Summary:")
    print(f"   {result.summary}")
    
    # Group issues
    issues_by_severity = {}
    issues_by_category = {}
    
    for issue in result.issues:
        sev = issue.severity.value
        cat = issue.category.value
        
        if sev not in issues_by_severity:
            issues_by_severity[sev] = []
        issues_by_severity[sev].append(issue)
        
        if cat not in issues_by_category:
            issues_by_category[cat] = []
        issues_by_category[cat].append(issue)
    
    # Display by severity
    print(f"\n🔴 Issues by Severity:")
    severity_order = ['critical', 'high', 'medium', 'low', 'info']
    for severity in severity_order:
        if severity in issues_by_severity:
            count = len(issues_by_severity[severity])
            icon = "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡" if severity == "medium" else "🔵"
            print(f"   {icon} {severity.upper():10s}: {count} issue(s)")
    
    # Detailed issues by category
    print(f"\n{'='*80}")
    print("DETAILED ISSUES BY CATEGORY")
    print(f"{'='*80}")
    
    for category in sorted(issues_by_category.keys()):
        issues = issues_by_category[category]
        cat_display = category.upper().replace('_', ' ')
        print(f"\n📂 {cat_display} ({len(issues)} issues)")
        print("-" * 80)
        
        for i, issue in enumerate(issues, 1):
            location = f"Line {issue.location.line_start}" if hasattr(issue, 'location') and issue.location else "N/A"
            
            print(f"\n   {i}. {issue.title}")
            print(f"      📍 Location: {location}")
            print(f"      🔴 Severity: {issue.severity.value.upper()}")
            print(f"      📝 Description: {issue.description}")
            
            if issue.code_snippet:
                print(f"      💻 Code: {issue.code_snippet[:100]}{'...' if len(issue.code_snippet) > 100 else ''}")
            
            print(f"      🎯 Confidence: {issue.confidence:.0%}")
            print(f"      🤖 Detected by: {issue.detected_by}")
    
    # Performance metrics
    print(f"\n{'='*80}")
    print("PERFORMANCE METRICS")
    print(f"{'='*80}")
    
    print(f"\n⏱️  Analysis Time: {result.analysis_time_seconds:.2f}s")
    print(f"🤖 Agents Used: {', '.join(result.analyzed_by)}")
    print(f"🔍 Total Issues: {len(result.issues)}")
    
    # Key insights
    print(f"\n{'='*80}")
    print("KEY INSIGHTS")
    print(f"{'='*80}")
    
    critical_issues = issues_by_severity.get('critical', [])
    if critical_issues:
        print(f"\n⚠️  CRITICAL SECURITY ISSUES FOUND ({len(critical_issues)}):")
        for issue in critical_issues:
            print(f"   - {issue.title} (Line {issue.location.line_start if issue.location else 'N/A'})")
    
    perf_issues = issues_by_category.get('performance', [])
    if perf_issues:
        print(f"\n🚀 PERFORMANCE IMPROVEMENTS NEEDED ({len(perf_issues)}):")
        for issue in perf_issues:
            print(f"   - {issue.title} (Line {issue.location.line_start if issue.location else 'N/A'})")
    
    quality_issues = issues_by_category.get('style', []) + issues_by_category.get('quality', [])
    if quality_issues:
        print(f"\n✨ CODE QUALITY IMPROVEMENTS ({len(quality_issues)}):")
        for issue in quality_issues:
            print(f"   - {issue.title} (Line {issue.location.line_start if issue.location else 'N/A'})")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    
    print(f"\n💡 Immediate Actions Required:")
    if critical_issues:
        print(f"   1. Fix {len(critical_issues)} critical security vulnerabilities")
        print(f"      → Use parameterized queries to prevent SQL injection")
        print(f"      → Move credentials to environment variables")
    
    if perf_issues:
        print(f"   2. Optimize {len(perf_issues)} performance bottlenecks")
        print(f"      → Use enumerate() instead of range(len())")
        print(f"      → Stream large files instead of reading into memory")
    
    if quality_issues:
        print(f"   3. Improve code quality ({len(quality_issues)} issues)")
        print(f"      → Use snake_case for function names (PEP 8)")
        print(f"      → Add proper documentation")
    
    print(f"\n{'='*80}")
    print(" "*25 + "✅ FLOW TEST COMPLETED")
    print(f"{'='*80}\n")
    
    return result


if __name__ == "__main__":
    result = asyncio.run(test_analysis_flow())
    
    # Exit with code based on critical issues
    critical_count = len([i for i in result.issues if i.severity.value == 'critical'])
    exit(1 if critical_count > 0 else 0)