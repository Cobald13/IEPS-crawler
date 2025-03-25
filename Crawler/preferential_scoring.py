# Preferential crawler del projekta

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import urlparse
from datetime import datetime

TARGET_DESCRIPTION = "ChatGPT"  # Change this to your domain/topic
vectorizer = CountVectorizer(stop_words='english')
vectorizer.fit([TARGET_DESCRIPTION])  # Fit once globally

def score_url_bow(link_tag):
    window_size = 50
    try:
        surrounding_text = link_tag.parent.text
        index = surrounding_text.find(link_tag.text)
        start = max(0, index - window_size)
        end = min(len(surrounding_text), index + window_size)
        surrounding_context = surrounding_text[start:end]

        texts = [TARGET_DESCRIPTION, surrounding_context]
        vectors = vectorizer.transform(texts)
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

        priority = 1 - similarity
        return priority
    except Exception as e:
        print(f"Error scoring link (BoW): {e}")
        return 1.0
    
def combined_score(link_tag, url, meta_keywords=None, last_accessed=None):      # Add meta_keywords and last_accessed
    bow_priority = score_url_bow(link_tag)

    # URL Depth
    path_depth = urlparse(url).path.count('/')
    depth_score = max(0, 3 - path_depth) * 0.02  # Bonus for shallow paths

    # Meta Tag Keyword Match
    meta_boost = -0.1 if meta_keywords and "chatgpt" and "openai" and "ai" and "Chat GPT" and "Open AI" and "DALL-E" and "umetna inteligenca" in meta_keywords.lower() else 0

    # Freshness (pages seen within 1 day get a boost)
    freshness_boost = 0
    if last_accessed:
        seconds_old = (datetime.utcnow() - last_accessed).total_seconds()
        if seconds_old < 86400:  # < 1 day
            freshness_boost = -0.05

    total_priority = bow_priority + depth_score + meta_boost + freshness_boost
    return float(max(0, total_priority))
