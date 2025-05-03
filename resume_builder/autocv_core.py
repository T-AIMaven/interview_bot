import os
from preprocess.jd_parser import extract_jd_info
from preprocess.resume_parser import parse_resume, read_pdf_text, parse_text_resume
from db.vector_db import ResumeVectorDB
from generate.resume_generator import create_resume_from_json
from generate.cover_letter_generator import create_cover_letter
from utils.prompt import get_skill_matching_prompt, generate_bullet_points_prompt, generate_cover_letter_prompt, generate_easy_prompt
from utils.llm_inference import llm_inference

class AutoCV:
    def __init__(self):
        self.resume_vector_db = ResumeVectorDB()

    def upload_resume(self, resume_file_name: str):
        """Upload resume to Pinecone vector database."""
        self.resume_content = parse_resume(resume_file_name)

        # Add resume experiences to Pinecone.
        for experience in self.resume_content["experiences"]:
            company = experience["company"]
            for bullet in experience["bullets"]:
                # Create embedding for the bullet point
                self.resume_vector_db.add_bullet_point(company, bullet)

        print("Experiences have been added to Pinecone.")

    def update_new_experience(self, jd_path: str, target: str = 'both'):
        """Update new experiences based on job description."""
        # Parse Job Description
        self.jd_info = extract_jd_info(jd_path)

        if target == 'both' or target == 'resume':
            for requirement in self.jd_info['required_skills']:
                skill = requirement['skill']
                results = self.resume_vector_db.search(skill, top_k=5)

                print("Search Results:")
                for match in results['matches']:
                    print(f"Company: {match['metadata']['company']}, Bullet: {match['metadata']['bullet']}")
                print("\n")

                # Checking skill match
                prompt = get_skill_matching_prompt(results, skill)
                response = llm_inference(prompt)
                print(f"Skill Match Response: {response}")

                # Determine the number of bullet points to generate
                if response == 'not-at-all' and requirement['priority'] == 'important':
                    cnt = 2
                if response == 'partially' and requirement['priority'] == 'important':
                    cnt = 1
                if response == 'not-at-all' and requirement['priority'] == 'nice-to-have':
                    cnt = 1
                
                # Generate bullet points based on the JD requirement
                prompt = generate_bullet_points_prompt(results, requirement, cnt)
                response = llm_inference(prompt)

                # Add generated bullet points to the vector database
                for experience in response:
                    self.resume_vector_db.add_bullet_point(experience["company"], experience["bullet"])

    def rewrite_resume(self, method: str = 'hard', resume_path: str = None):
        """Rewrite resume with new experiences."""
        # Extract top relevant experiences from the vector database
        if method == 'hard':
            relevant_experiences = dict()
            for skill in self.jd_info['required_skills']:
                skill_name = skill['skill']
                # Determine the number of top-k results to fetch based on priority
                if skill['priority'] == 'important':
                    k = 2
                else:
                    k = 1

                # Search for relevant experiences in the vector database
                results = self.resume_vector_db.search(skill_name, top_k=k)
                for match in results['matches']:
                    if relevant_experiences.get(match['metadata']['company']) is None:
                        relevant_experiences[match['metadata']['company']] = [match['metadata']['bullet']]
                    else:
                        relevant_experiences[match['metadata']['company']].append(match['metadata']['bullet'])
            
            # Update resume content with relevant experiences
            for company, bullets in relevant_experiences.items():
                # search the company in original resume content
                for exp in self.resume_content["experiences"]:
                    if exp["company"] == company:
                        # clear original bullet points
                        exp["bullets"] = []
                        # add the new bullet points to the original resume content
                        for bullet in bullets:
                            if bullet not in exp["bullets"]:
                                exp["bullets"].append(bullet)
                        break
        else:
            resume_txt = read_pdf_text(resume_path)
            with open('job_description.txt', 'r') as file:
                self.jd_info = file.read()
            
            prompt = generate_easy_prompt(self.jd_info, resume_txt)
            response = llm_inference(prompt, max_tokens=3000)

            self.resume_content = parse_text_resume(response)

    def write_cover_letter(self, resume, jd):
        """Write cover letter based on job description."""
        # Generate cover letter using the extracted information
        prompt = generate_cover_letter_prompt(jd, resume)
        response = llm_inference(prompt)
        
        return response

    def generate_output(self, jd_path: str, resume_path: str = None, target: str = 'both', output_dir: str = 'output', output_format: str = 'pdf', method: str = 'hard'):
        """Generate resume and cover letter based on job description."""
        # Generate new experiences based on job description
        if method == 'hard' and (target == 'both' or target == 'resume'):
            self.update_new_experience(jd_path, target)
            
        # Rewrite resume with new experiences
        self.rewrite_resume(method, resume_path)

        # Build cover_letter
        if target == 'both' or target == 'cover_letter':
            cover_letter = self.write_cover_letter(self.resume_content, self.jd_info)
        else:
            cover_letter = None

        # Generate final output
        return self.generate_final_output(self.jd_info, self.resume_content, cover_letter, output_dir, output_format, target)

    def generate_final_output(self, jd_info, resume_json, cover_letter, output_dir, output_format, target):
        """Generate the final output files."""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save Job Description as text file
        jd_path = os.path.join(output_dir, 'JobDescription.txt')
        with open(jd_path, 'w') as f:
            f.write(jd_info)

        # Create resume (DOCX & PDF)
        if target == 'both' or target == 'resume':
            resume_doc, resume_pdf = create_resume_from_json(resume_json, output_dir, output_format)

        # Create cover letter
        if target == 'both' or target == 'cover_letter':
            cover_letter_doc, cover_letter_pdf = create_cover_letter(cover_letter, output_dir, output_format)

        return {
            "resume_doc": resume_doc,
            "resume_pdf": resume_pdf,
            "cover_letter_doc": cover_letter_doc,
            "cover_letter_pdf": cover_letter_pdf,
            "job_description": jd_path
        }


# Example usage
if __name__ == "__main__":
    # Initialize AutoCVCore
    auto_cv = AutoCV(output_dir="output", output_format="docx")

    # Upload a resume
    auto_cv.upload_resume("example_resume.pdf")

    # Generate output based on a job description
    auto_cv.generate_output("example_job_description.txt", target="both")