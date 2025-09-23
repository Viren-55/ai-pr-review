#!/usr/bin/env python3
"""
Direct test of Azure OpenAI connection
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import time

# Load environment variables
load_dotenv("backend/.env")

def test_azure_connection():
    """Test direct connection to Azure OpenAI"""
    
    print("=" * 70)
    print("🔌 TESTING AZURE OPENAI CONNECTION")
    print("=" * 70)
    print()
    
    # Get credentials
    api_key = os.getenv("REASONING_AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("REASONING_AZURE_API_VERSION")
    model = os.getenv("REASONING_MODEL")
    
    print("📋 Configuration:")
    print(f"   Endpoint: {endpoint}")
    print(f"   API Version: {api_version}")
    print(f"   Model: {model}")
    print(f"   API Key: {'✅ Present' if api_key else '❌ Missing'}")
    print(f"   Key Length: {len(api_key) if api_key else 0} characters")
    print()
    
    if not all([api_key, endpoint, api_version, model]):
        print("❌ Missing required configuration!")
        return False
    
    try:
        print("🚀 Initializing Azure OpenAI client...")
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        print("✅ Client initialized successfully")
        print()
        
        # Test with a simple prompt
        print("📝 Testing with simple prompt...")
        test_prompt = "Analyze this Python code and identify issues: def add(a, b): return a + b"
        
        print(f"   Prompt: {test_prompt}")
        print()
        
        start_time = time.time()
        print("⏳ Sending request to Azure OpenAI...")
        
        # Try to make a completion request - o4-mini has specific parameter requirements
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a code review assistant. Analyze code for issues."},
                {"role": "user", "content": test_prompt}
            ],
            max_completion_tokens=500
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Response received in {elapsed:.2f} seconds")
        print()
        
        # Check response
        if response and response.choices:
            content = response.choices[0].message.content
            print("✅ SUCCESS - Azure OpenAI responded!")
            print()
            print("📄 Response Preview:")
            print("-" * 50)
            print(content[:300] + "..." if len(content) > 300 else content)
            print("-" * 50)
            print()
            
            # Check response metadata
            if hasattr(response, 'usage'):
                print("📊 Usage Stats:")
                print(f"   Prompt Tokens: {response.usage.prompt_tokens}")
                print(f"   Completion Tokens: {response.usage.completion_tokens}")
                print(f"   Total Tokens: {response.usage.total_tokens}")
            
            return True
        else:
            print("❌ Empty response from Azure OpenAI")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        
        # Check for common issues
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n⚠️  Authentication Error - Check your API key")
        elif "404" in str(e) or "not found" in str(e).lower():
            print("\n⚠️  Model/Deployment not found - Check your model name and deployment")
        elif "429" in str(e):
            print("\n⚠️  Rate limit exceeded - Too many requests")
        elif "timeout" in str(e).lower():
            print("\n⚠️  Request timed out - Network or service issue")
        else:
            print(f"\n⚠️  Unexpected error type: {type(e).__name__}")
        
        import traceback
        print("\n📝 Full Error Trace:")
        traceback.print_exc()
        
        return False

def test_with_code_issues():
    """Test Azure OpenAI with code containing specific issues"""
    
    print("\n" + "=" * 70)
    print("🔍 TESTING WITH CODE CONTAINING ISSUES")
    print("=" * 70)
    print()
    
    # Load environment
    api_key = os.getenv("REASONING_AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("REASONING_AZURE_API_VERSION")
    model = os.getenv("REASONING_MODEL")
    
    if not all([api_key, endpoint, api_version, model]):
        print("❌ Missing configuration")
        return False
    
    try:
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        
        # Code with obvious issues
        test_code = '''
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + str(user_id)  # SQL injection
    return execute_query(query)

PASSWORD = "admin123"  # Hardcoded password

def divide(a, b):
    return a / b  # No zero check
'''
        
        prompt = f"""Analyze this Python code and identify security, performance, and quality issues:

{test_code}

Provide a structured analysis with:
1. Security issues
2. Code quality issues
3. Best practice violations
"""
        
        print("📝 Sending code with known issues...")
        print("   Expected: SQL injection, hardcoded password, division by zero risk")
        print()
        
        start_time = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a code security and quality analyzer. Identify all issues in the code."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=1000
        )
        
        elapsed = time.time() - start_time
        print(f"⏱️  Analysis completed in {elapsed:.2f} seconds")
        print()
        
        if response and response.choices:
            analysis = response.choices[0].message.content
            print("📋 AI Analysis:")
            print("-" * 50)
            print(analysis)
            print("-" * 50)
            
            # Check if key issues were detected
            checks = {
                "SQL Injection": "sql" in analysis.lower() and "injection" in analysis.lower(),
                "Hardcoded Password": "password" in analysis.lower() or "hardcoded" in analysis.lower(),
                "Division by Zero": "zero" in analysis.lower() or "division" in analysis.lower()
            }
            
            print("\n✅ Issue Detection:")
            for issue, detected in checks.items():
                status = "✅" if detected else "❌"
                print(f"   {status} {issue}")
            
            return all(checks.values())
        
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Test basic connection
    connection_ok = test_azure_connection()
    
    # If connection works, test with actual code issues
    if connection_ok:
        issues_detected = test_with_code_issues()
        
        print("\n" + "=" * 70)
        if issues_detected:
            print("🎉 AZURE OPENAI IS WORKING CORRECTLY!")
            print("Connection successful and AI is detecting code issues properly.")
        else:
            print("⚠️  PARTIAL SUCCESS")
            print("Connection works but AI may not be detecting all issues.")
    else:
        print("\n" + "=" * 70)
        print("❌ AZURE OPENAI CONNECTION FAILED")
        print("Please check your credentials and network connection.")
    print("=" * 70)