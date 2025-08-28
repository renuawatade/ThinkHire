# matcher.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def match_job_to_candidates(job_text, candidate_texts, top_k=5):
    """
    Args:
      job_text (str): job description text
      candidate_texts (list[str]): list of resume raw-texts
      top_k (int): how many top matches to return

    Returns:
      list of tuples: [(candidate_index, score), ...] sorted by score desc.
      score is cosine similarity in [0.0, 1.0].
    """
    if not candidate_texts:
        return []

    # Build TF-IDF on (job + candidates)
    docs = [job_text] + candidate_texts
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf = vectorizer.fit_transform(docs)

    job_vec = tfidf[0:1]         # job vector
    cand_vecs = tfidf[1:]       # candidate vectors

    cosines = cosine_similarity(job_vec, cand_vecs).flatten()  # shape (n_candidates,)
    # sort indices by descending similarity
    sorted_idx = np.argsort(-cosines)

    results = [(int(i), float(cosines[i])) for i in sorted_idx[:top_k]]
    return results
