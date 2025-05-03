from .hyperbolic_llm_inference import get_hyperbolic_llm_response
from .openai_llm_inference import get_openai_llm_response

def llm_inference(prompt, model='hyperbolic', temperature=0.7, max_tokens=1000):
    """
    Perform inference using the specified LLM model.

    Args:
        model (str): The name of the LLM model to use ('hyperbolic' or 'openai').
        prompt (str): The input prompt for the LLM.
        temperature (float): Sampling temperature for the LLM.
        max_tokens (int): Maximum number of tokens to generate.

    Returns:
        str: The generated response from the LLM.
    """
    messages = [{"role": "user", "content": prompt}]

    if model == 'hyperbolic':
        return get_hyperbolic_llm_response(messages, temperature, max_tokens)
    elif model == 'openai':
        return get_openai_llm_response(messages, temperature, max_tokens)
    else:
        raise ValueError("Invalid model specified. Choose 'hyperbolic' or 'openai'.")