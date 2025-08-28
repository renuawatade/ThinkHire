import PyPDF2

# Function to extract text from a PDF
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

if __name__ == "__main__":
    # Replace 'resume.pdf' with your actual resume file name
    resume_text = extract_text_from_pdf("resume.pdf")

    # Print first 500 characters to check
    print("Extracted Resume Text (first 500 chars):")
    print(resume_text[:500])
