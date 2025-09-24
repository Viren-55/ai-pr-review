"""Simple test script to verify Azure OpenAI works with Pydantic AI."""

import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncAzureOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# Load environment variables
load_dotenv()

async def test_azure_openai():
    """Test Azure OpenAI with Pydantic AI."""
    
    # Step 1: Create AsyncAzureOpenAI client
    print("Step 1: Creating AsyncAzureOpenAI client...")
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv('REASONING_AZURE_OPENAI_ENDPOINT'),
        api_version=os.getenv('REASONING_AZURE_API_VERSION'),
        api_key=os.getenv('REASONING_AZURE_OPENAI_API_KEY'),
    )
    print(f"✅ Client created - Endpoint: {os.getenv('REASONING_AZURE_OPENAI_ENDPOINT')}")
    
    # Step 2: Create OpenAIChatModel with Azure provider
    print("\nStep 2: Creating OpenAIChatModel with Azure provider...")
    model = OpenAIChatModel(
        os.getenv('REASONING_MODEL', 'gpt-4'),
        provider=OpenAIProvider(openai_client=client),
    )
    print(f"✅ Model created - Deployment: {os.getenv('REASONING_MODEL')}")
    
    # Step 3: Create Pydantic AI Agent
    print("\nStep 3: Creating Pydantic AI Agent...")
    agent = Agent(
        model,
        system_prompt="You are a helpful code analysis assistant. Analyze code and find issues."
    )
    print("✅ Agent created")
    
    # Step 4: Test with simple code
    print("\nStep 4: Testing with simple Python code...")
    test_code = """
x = 5
y = 10
print(x + y)
"""
    
    prompt = f"""Analyze this Python code for any issues:

```python
{test_code}
```

Find issues like:
- Missing docstrings
- No type hints
- Using print() instead of logging
- Any other code quality issues

List each issue clearly."""

    print(f"Prompt: {prompt[:100]}...")
    
    # Step 5: Run the agent
    print("\nStep 5: Running agent...")
    result = await agent.run(prompt)
    
    print("\n" + "="*50)
    print("RESULT:")
    print("="*50)
    print("Result type:", type(result))
    print("Result attributes:", dir(result))
    print("\nResult data:", result.data if hasattr(result, 'data') else result)
    print("="*50)
    
    return result

if __name__ == "__main__":
    print("Testing Azure OpenAI with Pydantic AI\n")
    result = asyncio.run(test_azure_openai())
    print("\n✅ Test completed successfully!")