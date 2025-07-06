"""
Integration tests for LLM service.

These tests require real OpenRouter API credentials to be set in environment variables.
"""

import pytest
import os
from backend.services.llm.openrouter_client import OpenRouterClient
from backend.services.llm.generator import generate
from backend.services.llm.models import LLMRequest
from backend.core.llm_models import OPENROUTER_GPT_4_1, OPENROUTER_CLAUDE_4_SONNET


@pytest.mark.integration
def test_openrouter_client_initialization():
    """Test OpenRouter client initialization."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    assert api_key is not None  # Type assertion for linter
    client = OpenRouterClient(api_key=api_key)
    assert client.api_key == api_key
    assert client.base_url == "https://openrouter.ai/api/v1"
    assert "Authorization" in client.headers
    assert client.headers["Authorization"] == f"Bearer {api_key}"


@pytest.mark.integration
def test_llm_generation_simple():
    """Test basic LLM generation with OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    assert api_key is not None  # Type assertion for linter
    client = OpenRouterClient(api_key=api_key)
    request = LLMRequest(
        prompt="Say 'Hello' and nothing else",
        model=OPENROUTER_GPT_4_1,
        max_tokens=10,
        temperature=0.0
    )
    
    response = generate(client, request)
    
    assert response.content is not None
    assert len(response.content) > 0
    assert response.model == OPENROUTER_GPT_4_1
    assert response.usage is not None
    assert response.usage.total_tokens is not None
    assert response.usage.total_tokens > 0


@pytest.mark.integration
def test_llm_generation_with_usage():
    """Test LLM generation and verify usage statistics."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    assert api_key is not None  # Type assertion for linter
    client = OpenRouterClient(api_key=api_key)
    request = LLMRequest(
        prompt="Write a single sentence about cats",
        model=OPENROUTER_GPT_4_1,
        max_tokens=50,
        temperature=0.5
    )
    
    response = generate(client, request)
    
    assert response.content is not None
    assert len(response.content) > 0
    assert response.model == OPENROUTER_GPT_4_1
    
    # Check usage statistics
    assert response.usage is not None
    assert response.usage.prompt_tokens is not None
    assert response.usage.completion_tokens is not None
    assert response.usage.total_tokens is not None
    assert response.usage.total_tokens == response.usage.prompt_tokens + response.usage.completion_tokens


@pytest.mark.integration
def test_llm_generation_different_models():
    """Test LLM generation with different models."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    assert api_key is not None  # Type assertion for linter
    client = OpenRouterClient(api_key=api_key)
    
    # Test different models
    models = [OPENROUTER_GPT_4_1, OPENROUTER_CLAUDE_4_SONNET]
    
    for model in models:
        request = LLMRequest(
            prompt="Say 'Test' and nothing else",
            model=model,
            max_tokens=10,
            temperature=0.0
        )
        
        response = generate(client, request)
        
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == model


@pytest.mark.integration
def test_llm_rate_limiting_simulation():
    """Test that rate limiting logic works (using valid requests)."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")
    
    assert api_key is not None  # Type assertion for linter
    client = OpenRouterClient(api_key=api_key)
    
    # Make multiple requests quickly to potentially trigger rate limiting
    # This won't actually trigger rate limiting with gpt,
    # but tests the code path
    for i in range(3):
        request = LLMRequest(
            prompt=f"Say 'Request {i+1}' and nothing else",
            model=OPENROUTER_GPT_4_1,
            max_tokens=10,
            temperature=0.0
        )
        
        response = generate(client, request)
        assert response.content is not None
        assert len(response.content) > 0


if __name__ == "__main__":
    # Simple test runner for development
    def run_tests():
        """Run basic test for development."""
        print("Testing LLM service...")
        
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY not set")
            return
        
        try:
            client = OpenRouterClient(api_key=api_key)
            request = LLMRequest(
                prompt="Say 'Hello from LLM service!' and nothing else",
                model=OPENROUTER_GPT_4_1,
                max_tokens=20,
                temperature=0.0
            )
            
            response = generate(client, request)
            
            print(f"✅ LLM service working!")
            print(f"   Response: {response.content}")
            print(f"   Model: {response.model}")
            print(f"   Usage: {response.usage}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    run_tests() 