from typing import Optional
from pydantic import BaseModel, Field


class LLMRequest(BaseModel):
    """Request model for LLM generation"""
    prompt: str = Field(..., description="The prompt text to send to the LLM")
    model: str = Field(..., description="The LLM model to use")
    max_tokens: int = Field(default=1000, description="Maximum number of tokens to generate")
    temperature: float = Field(default=0.7, description="Temperature for response generation")
    
    class Config:
        frozen = True


class LLMUsage(BaseModel):
    """Usage statistics from LLM response"""
    prompt_tokens: Optional[int] = Field(None, description="Number of tokens in the prompt")
    completion_tokens: Optional[int] = Field(None, description="Number of tokens in the completion")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens used")
    
    class Config:
        frozen = True


class LLMResponse(BaseModel):
    """Response model from LLM generation"""
    content: str = Field(..., description="The generated text content")
    model: str = Field(..., description="The LLM model that was used")
    usage: Optional[LLMUsage] = Field(None, description="Usage statistics")
    
    class Config:
        frozen = True 