import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_hyperbolic_llm_response(messages: list[dict], temperature: float = 0.1, max_tokens = 512) -> dict:
    """
    Get response from Hyperbolic LLM API.
    
    Args:
        messages (list): List of message dictionaries with 'role' and 'content' keys.
        
    Returns:
        dict: JSON response from the API.
    """
    # Ensure messages are in the correct format
    if not isinstance(messages, list) or not all(isinstance(msg, dict) for msg in messages):
        raise ValueError("Messages must be a list of dictionaries.")
    
    # Define the API endpoint and headers
    url = "https://api.hyperbolic.xyz/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('HYPERBOLIC_API_KEY')}"
    }
    data = {
        "messages": messages,
        "model": "deepseek-ai/DeepSeek-V3",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content'].strip()