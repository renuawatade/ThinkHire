import re
import spacy
from difflib import SequenceMatcher

# Load spaCy model (ensure it's installed: python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

# -------------------- Skill Database --------------------
SKILLS_DB = [
    "Python", "Java", "C++", "C", "SQL", "MongoDB", "PostgreSQL",
    "JavaScript", "Node.js", "Express.js", "React", "HTML", "CSS",
    "Flask", "Django", "Machine Learning", "Deep Learning", "Data Analysis",
    "AWS", "Azure", "GCP", "Git", "Excel", "Power BI", "Tableau",
    "TensorFlow", "PyTorch", "NLP", "Data Visualization", "Leadership",
    "Communication", "Problem Solving", "Teamwork", "Docker", "Kubernetes"
]

# -------------------- Degree Patterns --------------------
DEGREE_PATTERNS = [
    (r"\bph\.?d\b|\bdoctorate\b", "PhD", 7),
    (r"\bm\.?tech\b|\bmtech\b|\bmaster\b|\bm\.?s\b|\bms\b|\bm\.?sc\b|\bmsc\b", "Master", 6),
    (r"\bmca\b", "MCA", 6),
    (r"\bmba\b", "MBA", 6),
    (r"\bb\.?tech\b|\bbtech\b|\bb\.?e\b|\bbe\b|\bbachelor\b|\bb\.?sc\b|\bbsc\b", "Bachelor", 5),
    (r"\bdiploma\b", "Diploma", 4),
    (r"\b12th\b|\bhigher secondary\b|\bsenior secondary\b", "Higher Secondary", 2),
    (r"\b10th\b|\bsecondary\b", "Secondary", 1),
]

# -------------------- Helper --------------------
def _clean(line: str) -> str:
    return " ".join(line.split()).strip()

# -------------------- Name Extraction --------------------
def extract_name(resume_text: str) -> str:
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
    for line in lines[:6]:
        if (2 <= len(line.split()) <= 4
            and not re.search(r"[@\d]|www\.|http", line, re.I)
            and re.search(r"[A-Z]", line)
            and not re.search(r"resume|curriculum vitae|cv", line, re.I)):
            return _clean(line)

    doc = nlp(" ".join(lines[:8]))
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return _clean(ent.text)
    return "Not Found"

# -------------------- Email Extraction --------------------
def extract_email(resume_text: str) -> str:
    email = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text)
    return email[0].strip() if email else "Not Found"

# -------------------- Phone Extraction --------------------
def extract_phone(resume_text: str) -> str:
    phones = re.findall(r"(\+?\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5})", resume_text)
    if phones:
        phones = [p.strip() for p in phones]
        phones.sort(key=lambda x: len(re.sub(r"\D", "", x)), reverse=True)
        return phones[0]
    return "Not Found"

# -------------------- Skill Extraction (Improved) --------------------
def extract_skills(resume_text: str, jd_text: str = "") -> list:
    resume_norm = re.sub(r"[\W_]+", " ", resume_text.lower())
    resume_text_lower = resume_text.lower()
    tokens = set(resume_norm.split())

    found = []
    for skill in SKILLS_DB:
        skill_lower = skill.lower()
        skill_norm = re.sub(r"[\W_]+", " ", skill_lower).strip()
        skill_words = skill_norm.split()

        # Exact substring match (most reliable)
        if skill_lower in resume_text_lower:
            found.append(skill)
            continue
        
        # All words present in normalized text
        if all(w in tokens for w in skill_words):
            found.append(skill)
            continue
        
        # Fuzzy match with lower threshold for partial matches
        for word in tokens:
            if len(word) > 2 and len(skill_norm) > 2:
                similarity = SequenceMatcher(None, word, skill_norm).ratio()
                if similarity > 0.75:  # Lowered from 0.8 for better detection
                    found.append(skill)
                    break

    return sorted(list(set(found))) if found else []

# -------------------- Education Extraction --------------------
def _find_years(text: str):
    m = re.search(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", text)
    if m:
        yrs = re.findall(r"(?:19|20)\d{2}", m.group(0))
        if len(yrs) >= 2:
            return (int(yrs[0]), int(yrs[1]))
    years = re.findall(r"\b(19|20)\d{2}\b", text)
    if years:
        all_years = re.findall(r"\b(?:19|20)\d{2}\b", text)
        if all_years:
            y = int(all_years[-1])
            return (None, y)
    return (None, None)

def extract_education(resume_text: str) -> str:
    lines = [_clean(l) for l in resume_text.splitlines() if l.strip()]
    candidates = []

    for idx, line in enumerate(lines):
        l_low = line.lower()
        if (any(re.search(pat, l_low, re.I) for pat,_,_ in DEGREE_PATTERNS)
            or re.search(r"\b(university|college|institute|school|academy|iit|nit|iiit|iim|bits)\b", l_low, re.I)
            or re.search(r"(?:19|20)\d{2}", l_low)):

            degree_label = None
            degree_level = 0
            for pat, label, level in DEGREE_PATTERNS:
                if re.search(pat, line, re.I):
                    degree_label, degree_level = label, level
                    break

            field = ""
            fmatch = re.search(r"(?:in|of)\s+([A-Za-z0-9 &\.\-+]+?)(?:,|\(| at | from | - |$)", line, re.I)
            if fmatch:
                field = _clean(fmatch.group(1))

            inst = ""
            inst_match = re.search(r"([A-Za-z0-9 &\.\-]+(?:University|College|Institute|School|IIT|NIT|IIIT|IIM|BITS|VIT|PES|SRM|COEP)[A-Za-z0-9 &\.\-]*)", line, re.I)
            if inst_match:
                inst = _clean(inst_match.group(0))
            else:
                alt = re.search(r"(?:at|from)\s+([A-Za-z0-9 &\.\-]+)", line, re.I)
                if alt:
                    inst = _clean(alt.group(1).split(",")[0])

            start_y, end_y = _find_years(line)

            candidates.append({
                "line": line,
                "idx": idx,
                "degree_label": degree_label,
                "degree_level": degree_level,
                "field": field,
                "institution": inst,
                "start_year": start_y,
                "end_year": end_y
            })

    if not candidates:
        return "Not Found"

    def cand_score(c):
        lvl = c.get("degree_level", 0) or 0
        endy = c.get("end_year") or 0
        return (lvl, endy, -c.get("idx", 0))

    candidates.sort(key=cand_score, reverse=True)
    best = candidates[0]

    parts = []
    deg = best.get("degree_label")
    if deg:
        parts.append(deg)
    fld = best.get("field")
    if fld:
        if "university" not in fld.lower() and "college" not in fld.lower():
            parts.append(f"in {fld}")
    inst = best.get("institution")
    if inst:
        parts.append(f"at {inst}")
    sy, ey = best.get("start_year"), best.get("end_year")
    if ey and sy:
        parts.append(f"({sy}–{ey})")
    elif ey:
        parts.append(f"({ey})")

    formatted = " ".join(parts).strip()
    return formatted or "Not Found"

# -------------------- Main Resume Parser --------------------
def parse_resume(resume_text: str, jd_text: str = "") -> dict:
    return {
        "name": extract_name(resume_text),
        "email": extract_email(resume_text),
        "phone": extract_phone(resume_text),
        "skills": extract_skills(resume_text, jd_text),
        "education": extract_education(resume_text),
    }
