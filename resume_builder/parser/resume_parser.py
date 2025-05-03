import os
import json
from typing import Dict, List, Union
from docx import Document
import pdfplumber
from dotenv import load_dotenv

from utils.prompt import parse_resume_prompt
from utils.llm_inference import llm_inference

load_dotenv()

def read_docx_text(path: str) -> List[str]:
    doc = Document(path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    text = "\n".join(lines)
    return text

def parse_docx_resume(path: str) -> Dict:
    return parse_text_resume(read_docx_text(path))

def read_pdf_text(path: str) -> List[str]:
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines += page.extract_text().split("\n")
    lines = [line.strip() for line in lines if line.strip()]
    text = "\n".join(lines)

    return text

def parse_pdf_resume(path: str) -> Dict:
    return parse_text_resume(read_pdf_text(path))

def parse_text_resume(text: str) -> Dict:
    prompt = parse_resume_prompt(text)

    response = llm_inference(prompt, temperature=0.0, max_tokens=2000)
    if response is None:
        raise ValueError("No response from LLM.")
    
    return eval(response)

def parse_resume(path: str) -> Dict:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return parse_docx_resume(path)
    elif ext == ".pdf":
        return parse_pdf_resume(path)
    else:
        raise ValueError("Unsupported file type")

if __name__ == "__main__":
    # Example usage
    resume_path = "andrew.pdf"  # Change this to your resume path
    parsed_resume = parse_resume(resume_path)
    # dump json to file
    with open("parsed_resume.json", "w") as f:
        json.dump(parsed_resume, f, indent=4)
    # print parsed resume
    print(parsed_resume)