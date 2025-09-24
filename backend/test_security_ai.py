"""Test security agent with AI parsing."""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from agents_v2.security_agent import SecurityAnalysisAgent
from agents_v2.models import CodeContext

load_dotenv()

async def test_security_agent():
    # Create Azure client
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv('REASONING_AZURE_OPENAI_ENDPOINT'),
        api_version=os.getenv('REASONING_AZURE_API_VERSION'),
        api_key=os.getenv('REASONING_AZURE_OPENAI_API_KEY'),
    )
    
    # Create security agent
    agent = SecurityAnalysisAgent(
        async_azure_client=client,
        model_name=os.getenv('REASONING_MODEL', 'gpt-4')
    )
    
    # Test code with multiple vulnerabilities
    test_code = '''
api_key = "sk-1234567890abcdef1234567890abcdef"
password = "admin123"

query = "SELECT * FROM users WHERE username = '" + username + "'"
cursor.execute(query)

data = pickle.loads(user_input)

os.system("rm -rf " + file_path)
'''
    
    context = CodeContext(
        code=test_code,
        language="python",
        file_path="test.py"
    )
    
    print("Testing Security Agent with AI Analysis...")
    print("=" * 60)
    
    response = await agent.analyze(context)
    issues = response.data
    
    print(f"\n✅ Analysis completed in {response.processing_time*1000:.2f}ms")
    print(f"Found {len(issues)} security issues:\n")
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue.title}")
        print(f"   Line: {issue.location.line_start}")
        print(f"   Severity: {issue.severity}")
        print(f"   Description: {issue.description}")
        print(f"   Code: {issue.code_snippet}")
        print()

if __name__ == "__main__":
    asyncio.run(test_security_agent())