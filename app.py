from flask import Flask, render_template, request
import os
import docx2txt
import pdfplumber

app = Flask(__name__)

# Function to extract text from different file types
def extract_text(file_path):
    text = ""

    # Handle PDF files
    if file_path.endswith(".pdf"):
        try:
            # Try with pdfplumber first
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            try:
                # Fallback: PyPDF2
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text += page.extract_text() or ""
            except Exception:
                try:
                    # Final fallback: PyMuPDF (fitz)
                    import fitz
                    doc = fitz.open(file_path)
                    for page in doc:
                        text += page.get_text("text") or ""
                    doc.close()
                except Exception as e:
                    text = f"[Could not read PDF: {e}]"

    # Handle DOCX files
    elif file_path.endswith(".docx"):
        text = docx2txt.process(file_path) or ""   # Avoid NoneType

    # Handle TXT files
    elif file_path.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read() or ""
        except UnicodeDecodeError:
            # fallback for Windows/ANSI encoded files
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read() or ""

    return text


# Very simple info extraction (improve later with NLP)
def extract_resume_info(text):
    info = {
        "Name": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
        "Skills": "Not Found",
        "Education": "Not Found"
    }

    # Basic examples (later we will improve with regex/NLP)
    lines = text.split("\n")

    # Try to get first non-empty line as name (temporary logic)
    for line in lines:
        if line.strip():
            info["Name"] = line.strip()
            break

    # Email extraction
    import re
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        info["Email"] = email_match.group(0)

    # Phone extraction
    phone_match = re.search(r"\+?\d[\d\s-]{8,}\d", text)
    if phone_match:
        info["Phone"] = phone_match.group(0)

    # Skills extraction (very basic: just checking keywords)
    skills_keywords = ["java", "python", "c++", "html", "css", "excel"]
    found_skills = [skill for skill in skills_keywords if skill.lower() in text.lower()]
    if found_skills:
        info["Skills"] = ", ".join(found_skills)

    # Education extraction (just checking words)
    edu_keywords = ["B.Tech", "M.Tech", "B.Sc", "M.Sc", "Bachelor", "Master", "Engineering", "College", "University"]
    found_edu = [edu for edu in edu_keywords if edu.lower() in text.lower()]
    if found_edu:
        info["Education"] = ", ".join(found_edu)

    return info


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part"
    file = request.files["file"]
    if file.filename == "":
        return "No selected file"
    
    # Save file
    filepath = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(filepath)

    # Extract text and info
    text = extract_text(filepath)
    resume_info = extract_resume_info(text)

    # Show extracted info
    return f"""
    <h2>Extracted Resume Info:</h2>
    <p><b>Name:</b> {resume_info['Name']}</p>
    <p><b>Email:</b> {resume_info['Email']}</p>
    <p><b>Phone:</b> {resume_info['Phone']}</p>
    <p><b>Skills:</b> {resume_info['Skills']}</p>
    <p><b>Education:</b> {resume_info['Education']}</p>
    """


if __name__ == "__main__":
    app.run(debug=True)
