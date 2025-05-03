import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_llm_response(messages: list[dict], temperature: float = 0.1, max_tokens = 512) -> str:
    """
    Get the response from OpenAI LLM using the provided prompt.
    :param prompt: The prompt to send to the LLM.
    :return: The response from the LLM.
    """

    # Ensure the OpenAI API key is set in the environment variables
    if "OPENAI_API_KEY" not in os.environ:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    # Initialize the OpenAI client and get the response
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content.strip()