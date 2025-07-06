import logging
import json
import requests
from .openrouter_client import OpenRouterClient
from .models import LLMRequest, LLMResponse, LLMUsage

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded error"""
    pass


class LLMQuotaError(LLMError):
    """Quota exceeded error"""
    pass


def generate(openrouter_client: OpenRouterClient, request: LLMRequest) -> LLMResponse:
    """
    Generate text using OpenRouter API with rate limiting and retries.
    
    Pure function that takes a client and request, returns response.
    Includes exponential backoff for rate limiting and error handling.
    """
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries + 1):
        try:
            return _make_llm_request(openrouter_client, request)
        except LLMRateLimitError as e:
            if attempt == max_retries:
                logger.error(f"Rate limit exceeded after {max_retries} attempts: {e}")
                raise
            
            # Exponential backoff for rate limiting
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
            import time
            time.sleep(delay)
            
        except requests.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code >= 500 and attempt < max_retries:
                # Server errors - retry with exponential backoff
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Server error {e.response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                import time
                time.sleep(delay)
            else:
                logger.error(f"HTTP error after {attempt + 1} attempts: {e}")
                status_code = e.response.status_code if hasattr(e, 'response') else 'unknown'
                raise LLMError(f"HTTP error: {status_code}")
                
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}")
            logger.error(f"Error details: {repr(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise LLMError(f"Unexpected error: {str(e)}")
    
    # Should never reach here
    raise LLMError("Maximum retries exceeded")


def _make_llm_request(openrouter_client: OpenRouterClient, request: LLMRequest) -> LLMResponse:
    """Make a single LLM request to OpenRouter API"""
    
    # Prepare request payload according to OpenRouter documentation
    payload = {
        "model": request.model,
        "messages": [
            {"role": "user", "content": request.prompt}
        ],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature
    }
    
    session = openrouter_client.get_session()
    
    try:
        # Use requests.post following OpenRouter examples
        response = session.post(
            f"{openrouter_client.base_url}/chat/completions",
            json=payload,
            timeout=30.0
        )
        response.raise_for_status()
        
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            # Rate limit exceeded
            raise LLMRateLimitError("Rate limit exceeded")
        elif e.response.status_code == 402:
            # Quota exceeded
            raise LLMQuotaError("Quota exceeded")
        else:
            # Other HTTP errors
            raise
    
    # Parse response
    try:
        response_data = response.json()
        
        # Extract content from OpenAI-compatible response
        if "choices" not in response_data or not response_data["choices"]:
            raise LLMError("No choices in API response")
        
        content = response_data["choices"][0]["message"]["content"]
        
        # Parse usage statistics if available
        usage = None
        if "usage" in response_data:
            usage_data = response_data["usage"]
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens"),
                completion_tokens=usage_data.get("completion_tokens"),
                total_tokens=usage_data.get("total_tokens")
            )
        
        return LLMResponse(
            content=content,
            model=request.model,
            usage=usage
        )
        
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse OpenRouter response: {e}")
        logger.error(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        raise LLMError(f"Failed to parse API response: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in _make_llm_request: {e}")
        logger.error(f"Error details: {repr(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise 