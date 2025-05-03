from docx import Document
from docx.shared import Pt
from docx2pdf import convert
import os

def create_resume_from_json(resume_json: dict, output_dir: str, output_format: str):
    # Create new document
    doc = Document()
    print(type(resume_json))
    print(resume_json)

    print('*' * 80)
    
    # Title
    doc.add_heading(f"{resume_json['name']} Resume", 0)

    # Summary section
    doc.add_heading("Summary", level=1)
    doc.add_paragraph(resume_json['summary'])

    # Skills section
    doc.add_heading("Skills", level=1)
    for skill in resume_json['skills']:
        doc.add_paragraph(f"{skill} : {', '.join(resume_json['skills'][skill])[:-2]}", style="List Bullet")

    # Experience section
    doc.add_heading("Professional Experience", level=1)
    
    for exp in resume_json['experiences']:
        doc.add_heading(f"{exp['company']} ({exp['role']})", level=2)
        doc.add_paragraph(f"{exp['start_date']} - {exp['end_date']}")
        for bullet in exp['bullets']:
            doc.add_paragraph(f"{bullet}", style="List Bullet")
    
    # Education section
    doc.add_heading("Education", level=1)
    for edu in resume_json['education']:
        doc.add_heading(f"{edu['institute_name']} ({edu['degree']})", level=2)
        doc.add_paragraph(f"{edu['start_date']} - {edu['end_date']}")
        if edu.get('gpa', None):
            doc.add_paragraph(f"GPA: {edu['gpa']}")
    
    # Save DOCX
    doc_path = os.path.join(output_dir, f"{resume_json['name']} Resume.docx")
    doc.save(doc_path)

    # Convert to PDF
    pdf_path = os.path.join(output_dir, f"{resume_json['name']} Resume.pdf")
    convert(doc_path, pdf_path)

    return doc_path, pdf_path
