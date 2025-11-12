from sentence_transformers import SentenceTransformer, util
import numpy as np
import re

model = SentenceTransformer("all-MiniLM-L6-v2")

SKILLS_DB = [
    "Python", "Java", "C++", "C", "SQL", "MongoDB", "PostgreSQL",
    "JavaScript", "Node.js", "Express.js", "React", "HTML", "CSS",
    "Flask", "Django", "Machine Learning", "Deep Learning", "Data Analysis",
    "AWS", "Azure", "GCP", "Git", "Excel", "Power BI", "Tableau",
    "TensorFlow", "PyTorch", "NLP", "Data Visualization", "Leadership",
    "Communication", "Problem Solving", "Teamwork", "Docker", "Kubernetes"
]

# ---------------- Resume Matching ---------------- #
def match_job_to_candidates(job_text, candidate_texts, top_k=5):
    if not candidate_texts:
        return []

    job_vec = model.encode(job_text, convert_to_tensor=True)
    cand_vecs = model.encode(candidate_texts, convert_to_tensor=True)
    cosines = util.cos_sim(job_vec, cand_vecs).cpu().numpy().flatten()

    job_skills = [s.lower() for s in SKILLS_DB if s.lower() in job_text.lower()]

    results = []
    for i, score in enumerate(cosines):
        # keep score in 0..1 range (cosine may be slightly negative)
        try:
            scaled_score = float(score)
        except Exception:
            scaled_score = 0.0
        if scaled_score < 0:
            scaled_score = 0.0

        # normalize resume and skill strings for matching (robust to punctuation)
        resume_lower = re.sub(r"[\W_]+", " ", candidate_texts[i].lower())
        matched_skills = [s for s in job_skills if re.sub(r"[\W_]+", " ", s) in resume_lower]

        # boost score more aggressively based on skill overlap to differentiate candidates
        if job_skills:
            skill_match_ratio = len(matched_skills) / len(job_skills)
            # add boost: 30% per matched skill (up to +100% for perfect match)
            boost = min(1.0, skill_match_ratio * 1.0)
            scaled_score = min(1.0, scaled_score * 0.6 + boost * 0.4)  # blend semantic + skill scores

        results.append((i, round(float(scaled_score), 4)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results

# ---------------- Resume Suggestions ---------------- #
def suggest_improvements(job_text, resume_text, resume_skills=None):
    """Return a list of human-friendly suggestions. If resume_skills (list)
    is provided, use it to determine missing skills; otherwise fall back to
    text matching.
    """
    suggestions = []
    # normalize job and resume text for robust matching
    job_norm = re.sub(r"[\W_]+", " ", job_text.lower())
    resume_lower = re.sub(r"[\W_]+", " ", resume_text.lower())

    # normalize provided parsed skills for comparison
    parsed_skills_norm = set()
    if resume_skills:
        for s in resume_skills:
            parsed_skills_norm.add(re.sub(r"[\W_]+", " ", s.lower()))

    # skills mentioned in JD but missing from resume (use parsed skills if available)
    missing_skills = []
    for s in SKILLS_DB:
        s_norm = re.sub(r"[\W_]+", " ", s.lower())
        if s_norm in job_norm:
            if parsed_skills_norm:
                if s_norm not in parsed_skills_norm:
                    missing_skills.append(s)
            else:
                if s_norm not in resume_lower:
                    missing_skills.append(s)

    if missing_skills:
        missing_str = ", ".join(missing_skills[:3])
        suggestions.append(f"Missing skills: {missing_str}")

    # contact & experience suggestions (per-resume checks)
    contact_missing = []
    if "@" not in resume_text:
        contact_missing.append("email")
    if not re.search(r"\+?\d[\d\s-]{8,}\d", resume_text):
        contact_missing.append("phone")
    if contact_missing:
        suggestions.append(f"Add contact info: {', '.join(contact_missing)}")
    
    if not re.search(r"\d+\s*(years|year|months|month)", resume_lower):
        suggestions.append("Clarify work experience duration.")

    # If the resume already has most of the JD skills, give a positive note
    if parsed_skills_norm:
        overlap = [s for s in SKILLS_DB if re.sub(r"[\W_]+", " ", s.lower()) in parsed_skills_norm and re.sub(r"[\W_]+", " ", s.lower()) in job_norm]
        if len(overlap) >= 3:
            suggestions.append(f"Strong skills match: {', '.join(overlap[:4])}")

    if not suggestions:
        suggestions.append("Resume is well-aligned with the job description.")

    return suggestions
