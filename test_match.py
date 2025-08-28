# test_match.py
from matcher import match_job_to_candidates

resumes = [
    "KIRAN DHAMANDE\nSkills: Java, C++, HTML, Excel\nExperience: 2 years in software dev",
    "Alice Smith\nSkills: Python, Machine Learning, SQL\nExperience: 3 years in data science",
    "Bob Kumar\nSkills: Java, Spring, Docker\nExperience: 4 years in backend"
]

job = "Looking for a Java developer experienced with Spring and Docker. 3+ years preferred."

matches = match_job_to_candidates(job, resumes, top_k=3)
print("Matches (candidate_index, score):")
for idx, score in matches:
    print(idx, round(score, 4))
