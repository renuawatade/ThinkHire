from flask import Flask, render_template, request
import os
import docx2txt
import pdfplumber
import zipfile

app = Flask(__name__)

# Function to extract text from different file types
def extract_text(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        try:
            # First try pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except Exception:
            # Fallback to PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text += page.extract_text() or ""
            except Exception as e:
                text = f"[Could not read PDF: {e}]"

    elif file_path.endswith(".docx"):
        text = docx2txt.process(file_path) or ""   # Avoid NoneType

    elif file_path.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read() or ""
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read() or ""

    return text

# Simple resume info extraction
def extract_resume_info(text):
    info = {
        "Name": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
        "Skills": "Not Found",
        "Education": "Not Found"
    }

    lines = text.split("\n")

    for line in lines:
        if line.strip():
            info["Name"] = line.strip()
            break

    import re
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        info["Email"] = email_match.group(0)

    phone_match = re.search(r"\+?\d[\d\s-]{8,}\d", text)
    if phone_match:
        info["Phone"] = phone_match.group(0)

    skills_keywords = ["java", "python", "c++", "html", "css", "excel"]
    found_skills = [skill for skill in skills_keywords if skill.lower() in text.lower()]
    if found_skills:
        info["Skills"] = ", ".join(found_skills)

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
    os.makedirs("uploads", exist_ok=True)

    # Handle JD input
    jd_text = request.form.get("jd_text", "")

    jd_file = request.files.get("jd_file")
    if jd_file and jd_file.filename != "":
        jd_path = os.path.join("uploads", jd_file.filename)
        jd_file.save(jd_path)
        jd_text += "\n" + extract_text(jd_path)

    # Handle ZIP file
    zip_file = request.files.get("zip_file")
    resumes_info = []

    if zip_file and zip_file.filename != "":
        zip_path = os.path.join("uploads", zip_file.filename)
        zip_file.save(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("uploads/")
            for filename in zip_ref.namelist():
                file_path = os.path.join("uploads", filename)
                if filename.lower().endswith((".pdf", ".docx", ".txt")):
                    text = extract_text(file_path)
                    info = extract_resume_info(text)
                    info["FileName"] = filename
                    resumes_info.append(info)

    # Handle single resume if ZIP not uploaded
    single_file = request.files.get("file")
    if single_file and single_file.filename != "" and not resumes_info:
        filepath = os.path.join("uploads", single_file.filename)
        single_file.save(filepath)
        text = extract_text(filepath)
        info = extract_resume_info(text)
        info["FileName"] = single_file.filename
        resumes_info.append(info)

    # Display results
    result_html = "<h2>Extracted Resume Info:</h2>"
    for info in resumes_info:
        result_html += f"""
        <p><b>File:</b> {info['FileName']}</p>
        <p><b>Name:</b> {info['Name']}</p>
        <p><b>Email:</b> {info['Email']}</p>
        <p><b>Phone:</b> {info['Phone']}</p>
        <p><b>Skills:</b> {info['Skills']}</p>
        <p><b>Education:</b> {info['Education']}</p>
        <hr>
        """

    result_html += "<h2>Extracted Job Description:</h2>"
    result_html += f"<pre>{jd_text}</pre>"

    return result_html

if __name__ == "__main__":
    app.run(debug=True)
