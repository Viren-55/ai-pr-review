"""Test all Pydantic AI agents with fixed tool signatures."""

import asyncio
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents_v2.security_agent import SecurityAnalysisAgent
from agents_v2.code_analyzer_agent import CodeAnalyzerAgent
from agents_v2.performance_agent import PerformanceAnalysisAgent
from agents_v2.fix_agent import CodeFixAgent
from agents_v2.editor_agent import CodeEditorAgent
from agents_v2.models import CodeContext

# Load environment variables
load_dotenv()


async def test_agent(agent_class, agent_name, test_code, context):
    """Test a single agent."""
    print(f"\n{'='*60}")
    print(f"Testing {agent_name}")
    print(f"{'='*60}")
    
    try:
        # Initialize agent
        azure_client = AzureOpenAI(
            api_key=os.getenv("REASONING_AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("REASONING_AZURE_API_VERSION"),
            azure_endpoint=os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
        )
        model_name = os.getenv("REASONING_MODEL")
        
        agent = agent_class(azure_client=azure_client, model_name=model_name)
        print(f"✅ {agent.name} initialized")
        
        # Run analysis
        result = await agent.analyze(context)
        
        if result.success:
            issues = result.data if isinstance(result.data, list) else []
            print(f"✅ Analysis completed in {result.processing_time:.3f}s")
            print(f"   Issues found: {len(issues)}")
            
            if issues:
                for i, issue in enumerate(issues[:3], 1):  # Show first 3 issues
                    print(f"\n   {i}. {issue.title}")
                    print(f"      Severity: {issue.severity.value}")
                    print(f"      Line: {issue.location.line_start if hasattr(issue, 'location') else 'N/A'}")
                
                if len(issues) > 3:
                    print(f"\n   ... and {len(issues) - 3} more issues")
            
            return True
        else:
            print(f"❌ Analysis failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Test all agents."""
    print("\n" + "="*60)
    print("TESTING ALL PYDANTIC AI AGENTS")
    print("="*60)
    
    # Test code with multiple issues
    test_code = """
def getUserData(username):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    result = cursor.fetchone()
    
    # Hardcoded credentials
    api_key = "sk-1234567890abcdefghijklmnop"
    password = "MySecretPassword123"
    
    # Inefficient loop
    for i in range(len(result)):
        print(result[i])
    
    # Reading entire file
    with open('data.txt') as f:
        data = f.read()
    
    # Poor naming convention (camelCase function)
    return result
"""
    
    print(f"\n📝 Test code ({len(test_code)} chars)")
    print("-" * 60)
    print(test_code)
    print("-" * 60)
    
    context = CodeContext(
        code=test_code,
        language="python",
        file_path="test.py"
    )
    
    # Test all agents
    agents_to_test = [
        (SecurityAnalysisAgent, "SecurityAnalysisAgent"),
        (CodeAnalyzerAgent, "CodeAnalyzerAgent"),
        (PerformanceAnalysisAgent, "PerformanceAnalysisAgent"),
        (CodeFixAgent, "CodeFixAgent"),
        (CodeEditorAgent, "CodeEditorAgent"),
    ]
    
    results = {}
    
    for agent_class, agent_name in agents_to_test:
        success = await test_agent(agent_class, agent_name, test_code, context)
        results[agent_name] = success
    
    # Summary
    print(f"\n\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for agent_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {agent_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n{passed}/{total} agents passed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())