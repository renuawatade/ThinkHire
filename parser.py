import re
import spacy

# Load spacy model
nlp = spacy.load("en_core_web_sm")

# Pre-defined skills database (expand as needed)
SKILLS_DB = [
    "Python", "Java", "SQL", "C++", "Machine Learning",
    "Deep Learning", "HTML", "CSS", "JavaScript",
    "Flask", "Django", "NLP", "Data Analysis", "Excel"
]

def extract_name(resume_text):
    doc = nlp(resume_text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    # fallback → first two words (assuming name at start)
    first_line = resume_text.strip().split("\n")[0]
    possible_name = " ".join(first_line.split()[:2])
    return possible_name if possible_name else None

def extract_email(resume_text):
    email = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
    return email[0] if email else None

def extract_phone(resume_text):
    phone = re.findall(r"(\+?\d{1,3}[-.\s]?\d{3,5}[-.\s]?\d{4,10})", resume_text)
    return phone[0] if phone else None

def extract_skills(resume_text):
    resume_text_lower = resume_text.lower()
    found = []
    for skill in SKILLS_DB:
        # use regex for whole word match
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", resume_text_lower):
            found.append(skill)
    return list(set(found)) if found else None

def extract_education(resume_text):
    education_keywords = [
        "B.Tech", "Bachelor", "Master", "MBA", "M.Tech", 
        "PhD", "Degree", "Diploma"
    ]
    found = []
    resume_text_lower = resume_text.lower()
    for word in education_keywords:
        if word.lower() in resume_text_lower:
            found.append(word)
    return list(set(found)) if found else None

def parse_resume(resume_text):
    return {
        "name": extract_name(resume_text),
        "email": extract_email(resume_text),
        "phone": extract_phone(resume_text),
        "skills": extract_skills(resume_text),
        "education": extract_education(resume_text)
    }

# Example usage
if __name__ == "__main__":
    sample_resume = """
    John Doe
    Email: john.doe@example.com
    Phone: +91 98765 43210
    Skills: Python, Java, SQL, Machine Learning, Django
    Education: B.Tech in Computer Science, MBA in Marketing
    """
    print(parse_resume(sample_resume))
