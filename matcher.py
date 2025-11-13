import re
import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load semantic model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define helper functions
def extract_years_of_experience(text):
    match = re.search(r'(\d+)\s*(?:\+)?\s*(?:years?|yrs?)', text.lower())
    return int(match.group(1)) if match else 0

def extract_skills(text):
    common_skills = [
        "python", "java", "c++", "c", "javascript", "html", "css", "react",
        "node.js", "express", "mongodb", "sql", "postgresql", "aws", "azure",
        "gcp", "docker", "flask", "machine learning", "data analysis",
        "git", "tensorflow", "tableau", "communication", "leadership"
    ]
    text_lower = text.lower()
    return [skill for skill in common_skills if skill in text_lower]

def match_job_to_candidates(job_description, resumes, top_k=5):
    # Encode job description and resumes for semantic similarity
    job_embedding = model.encode(job_description, convert_to_tensor=True)
    resume_embeddings = model.encode(resumes, convert_to_tensor=True)

    # Compute semantic similarity scores
    similarity_scores = util.pytorch_cos_sim(job_embedding, resume_embeddings)[0].cpu().numpy()

    # Extract job keywords and experience
    job_skills = extract_skills(job_description)
    job_experience = extract_years_of_experience(job_description)

    results = []
    for i, resume_text in enumerate(resumes):
        # Extract resume skills and experience
        resume_skills = extract_skills(resume_text)
        resume_experience = extract_years_of_experience(resume_text)

        # Skill matching score
        skill_overlap = len(set(resume_skills) & set(job_skills))
        total_skills = len(set(job_skills)) or 1
        skill_score = skill_overlap / total_skills

        # Experience matching score
        exp_score = min(resume_experience / job_experience, 1.0) if job_experience > 0 else 0.5

        # Combine scores
        final_score = (0.7 * similarity_scores[i]) + (0.2 * skill_score) + (0.1 * exp_score)
        results.append((i, final_score))

    # Sort by final score
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def suggest_improvements(job_text, resume_text, resume_skills=None):
    """Return a list of human-friendly suggestions for resume improvement."""
    suggestions = []
    
    # normalize text for matching
    job_norm = re.sub(r"[\W_]+", " ", job_text.lower())
    resume_lower = resume_text.lower()

    # List of all known skills
    all_skills = [
        "Python", "Java", "C++", "C", "SQL", "MongoDB", "PostgreSQL",
        "JavaScript", "Node.js", "Express.js", "React", "HTML", "CSS",
        "Flask", "Django", "Machine Learning", "Deep Learning", "Data Analysis",
        "AWS", "Azure", "GCP", "Git", "Excel", "Power BI", "Tableau",
        "TensorFlow", "PyTorch", "NLP", "Data Visualization", "Leadership",
        "Communication", "Problem Solving", "Teamwork", "Docker", "Kubernetes"
    ]

    # Find missing skills
    if resume_skills:
        parsed_skills_lower = set(s.lower() for s in resume_skills)
        missing_skills = []
        
        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower in job_norm and skill_lower not in parsed_skills_lower:
                missing_skills.append(skill)
        
        if missing_skills:
            suggestions.append(f"Missing skills: {', '.join(missing_skills[:3])}")

    # Check for contact info
    contact_missing = []
    if "@" not in resume_text:
        contact_missing.append("email")
    if not re.search(r"\+?\d[\d\s-]{8,}\d", resume_text):
        contact_missing.append("phone")
    if contact_missing:
        suggestions.append(f"Add contact info: {', '.join(contact_missing)}")

    # Check for experience duration
    if not re.search(r"\d+\s*(years|year|months|month)", resume_lower):
        suggestions.append("Clarify work experience duration.")

    # Check for strong skills match
    if resume_skills:
        overlap_count = sum(1 for s in resume_skills for skill in all_skills 
                          if s.lower() == skill.lower() and skill.lower() in job_norm)
        if overlap_count >= 3:
            overlap_skills = [s for s in resume_skills for skill in all_skills
                            if s.lower() == skill.lower() and skill.lower() in job_norm]
            suggestions.append(f"Strong skills match: {', '.join(overlap_skills[:4])}")

    if not suggestions:
        suggestions.append("Resume is well-aligned with the job description.")

    return suggestions
