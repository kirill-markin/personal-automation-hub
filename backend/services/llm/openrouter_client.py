import requests


class OpenRouterClient:
    """OpenRouter API client - simple connector to external system"""
    
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_session(self) -> requests.Session:
        """Get requests session for making requests"""
        session = requests.Session()
        session.headers.update(self.headers)
        return session 