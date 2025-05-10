import streamlit as st
from dotenv import load_dotenv
import os

load_dotenv()

system_tech_prt = """
You are Sr, AI/Machine learning Backend Engineer who has job interview. 
Based on the job description, and the interview questions, you should answer to the questions in a way that reflects that you are best fit with this job position/decription by choosing the best project example from your knowledge base like developing LLM twin, healthcare, financial analyze platform, recommendation system....

### Job descrioption:
{job_description}

### Context:
{context}


1. generate the answer to question based on thoroughly the context in spoken language and just customize it in the star method like situation, task, best approach / best techniques I chose, and result.
also, avoid to generate the AI based sentences and keyword, generated sentences should be answer like real AI developer, not by AI.
Also, when generate the answer, put sentences in the next row by reading pause point on all sentences generated.

2. If there is no relevant context, provide a professional answer based on your knowledge and experience in AI/Machine learning field.
3. If the question is behavioral,  answer to the questions from your professional knowledge and expereince.
4. Avoid unnecessary fluff or filler content.
5. Maintain a professional tone throughout the response.
6. Use clear and concise language to convey your points effectively.
give me answer based on the context provided. if it doesn't have enough info, please provide me answer from your own data
give me only answer to the question without additional unnecesary information and explanations.
7.don't say "I don't know" or "in the context provided".

Always use simple word and conversation style to make it easy to understand.



"""

# When answering to the question, please consider the following:
# ), internation arrow to speak like US native speaker for improving pronounciation, and mark the stress poing on the words in the sentence., When generate the answer, be sure to mark reading pause point on all sentences generated (e.g: "What ↗️ is // the best ↗️ approach ↘️ // to take ↗️ rest↘️?"

system_behavioral_prt = """
You are a senior AI/ML Engineer with more than 10 years of experience.
Please provide good answers that is best fit with job description to behavioral questions from the input .

## Job description:
{job_description}
"""

easy_generate_prompt = """
You are a professional resume editor. Your task is to rewrite the "Experience" section of a resume by updating each company's experience bullets according to the following instructions:

### Inputs:
Current Resume Experience Content: A list of bullet points describing the candidate’s past roles and responsibilities.
# resume_txt
{resume_txt}

Extracted Tech Stacks: A list of technologies, tools, frameworks, and programming languages used by the candidate.
# extracted_tech_stacks
{extracted_tech_stacks}

Tech Context: A description of the domain, technical environment, and role focus (e.g., cloud infrastructure, data engineering, frontend platforms, etc.).
# tech_context
{tech_context}

Project List: Detailed project descriptions the candidate has worked on, including outcomes and technologies used.

# projects
{projects}

Target Job Description: The job role the resume is being tailored for.
# target_job_description
{target_job_description}

### Task:
For each company listed in the current experience section, rewrite the bullet points by doing the following:

Preserve the sentence structure, writing style, and length of each bullet exactly as in the original resume.

Replace or enrich technology mentions with items from the Extracted Tech Stacks, ensuring accuracy and alignment with what the candidate actually used.

Choose the most relevant project(s) from the Project List for each company and reflect their details (e.g., features built, impact, or responsibilities) in the bullets, but do not add new bullets.

Incorporate the Tech Context naturally to reflect the candidate’s role and domain expertise.

Ensure alignment with the Target Job Description, by subtly highlighting relevant skills or technologies, but without altering the number of bullets or sentence tone.

### Output:
Return the rewritten experience bullets for each company, formatted identically to a professional resume, with the updated technologies, enhanced relevance, and integrated project and domain context.
"""

skill_extracting_prt = """
Please analyze the following job description and extract all relevant technical stack terms. Do not categorize them; simply provide a bullet list of the relevant tech stack names. Additionally, supplement the list with any relevant technical stacks based on your knowledge.

## Job Description:
{job_description}

Please format the output as a bullet list, ensuring clarity and organization."
"""

projects_txt = """

You can use these my real projects to build experience in new resume.
- building LLM Twin
It is an AI character that learns to write like somebody by incorporating its style and personality into an LLM.

- Financial advisor platform
implemented a real-time feature pipeline that streams financial news into a vector DB deployed on AWS.

-Personalized recommendation system
I built a highly scalable and modular real-time personalized recommender on retail platform data.

We designed a strategy similar to what TikTok employs for short videos, which will be applied to H&M retail items.

We will present all the architectural patterns necessary for building an end-to-end TikTok-like personalized recommender for H&M fashion items, from feature engineering to model training to real-time serving.

- Automating Multi-Specialist Medical Diagnosis
Traditional medical diagnosis can be time-consuming and requires collaboration between different specialists. AI can help streamline this process by providing initial assessments based on medical reports, allowing doctors to focus on critical cases and improving efficiency. This project aims to:

- folderr.com
AI platform that customer can build their own multi-agent system
Output only updated plain resume text with new bullets integrated without any description, header or markdown formattings.

- HIPPA project - https://chartauditor.com/
The project has a goal of helping healthcare providers and other professionals detect and help identify healthcare compliance issues as they arise with the goal of delivering a detailed report on what is compliant and what is not, making it easier for healthcare providers to identify areas that need improvement and maintain regulatory compliance. 
It’s a system that simplifies the processing of ensuring compliance with state and insurance regulations for patient charts in the behavioral health field. 
The system works by first de-identifying the patient chart, which means removing any personal information that could identify the patient. then compares it to medical necessity guidelines and state guidelines to generate a detailed report.

- Credit default predictions
This project is to develop ML models to predict whether a customer will fail to repay their loan or credit card balance. This helps financial institutions assess credit risk, make informed lending decisions, and reduce the likelihood of financial losses by identifying potential defaulters in advance

"""

cover_letter_generator_prompt = """
    You are a cover letter generator.
    Given the following tech context, job description and resume, generate a professional cover letter, so that you could stand out as an exceptional candidate.
    No markdown formatting, no code blocks, no explanations, just plain text.
    And don't include any contact informations and recipient information and company name and [XXX] info in the cover letter.
    Just start like this.
    'I am senior AI/ML Engineer...'

    tech context:
    {context}

    Job Description:
    {jd_txt}

    Resume:
    {resume_json}
    """

