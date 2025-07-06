"""
LLM model constants for the Personal Automation Hub.

This module defines all model names used throughout the application
to ensure consistency and easy updates.
"""

# OpenAI models
GPT_4_1 = "gpt-4.1"

# Anthropic models
CLAUDE_4_SONNET = "claude-sonnet-4"

# OpenRouter model paths
OPENROUTER_GPT_4_1 = f"openai/{GPT_4_1}"
OPENROUTER_CLAUDE_4_SONNET = f"anthropic/{CLAUDE_4_SONNET}"

# Default models for different use cases
DEFAULT_CATEGORIZATION_MODEL = OPENROUTER_GPT_4_1
DEFAULT_DRAFT_GENERATION_MODEL = OPENROUTER_CLAUDE_4_SONNET