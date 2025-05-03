from utils.llm_inference import llm_inference
from utils.prompt import job_description_prompt

def extract_jd_info(jd_text: str) -> dict:
    prompt = job_description_prompt.format(jd_text=jd_text)

    response = llm_inference(prompt, model='hyperbolic', temperature=0.0, max_tokens=2000)
    if response is None:
        raise ValueError("No response from LLM.")
    
    return eval(response)

if __name__ == "__main__":
    with open('job_description.txt', 'r') as file:
        jd_text = file.read()
    
    jd_info = extract_jd_info(jd_text)
    print(jd_info)