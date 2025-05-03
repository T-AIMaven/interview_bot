import os
from docx import Document
from docx2pdf import convert

def create_cover_letter(cover_letter: str, output_dir: str, output_format: str = "docx") -> str:
    # Save cover letter
    doc_path = os.path.join(output_dir, f"Cover Letter.docx")
    doc = Document()
    doc.add_paragraph(cover_letter)
    doc.save(doc_path)

    # Convert to PDF
    pdf_path = os.path.join(output_dir, f"Cover Letter.pdf")
    convert(doc_path, pdf_path)

    return doc_path, pdf_path
