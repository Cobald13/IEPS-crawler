# Preferential crawler del projekta

from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import urlparse
from datetime import datetime

TARGET_DESCRIPTION = "slo-tech forum razprave članki trendi umetna inteligenca strojna oprema programska oprema"
slovene_stop_words = [
    "in", "ali", "je", "se", "za", "na", "da", "s", "so", "kot", "ki", "po", "z", "ob"
]
vectorizer = CountVectorizer(stop_words=slovene_stop_words)
vectorizer.fit([TARGET_DESCRIPTION])  # Fit once globally

slovene_keywords = [
        "računalništvo", "strojna oprema", "programska oprema", "operacijski sistem", "varnost",
        "hekanje", "splet", "umetna inteligenca", "robotika", "algoritmi", "računalniška omrežja",
        "internet", "novice", "članki", "trendi", "diskusija", "forum", "debata", "računalniki",
        "mobilne naprave", "pametni telefoni", "android", "linux", "windows", "open source",
        "prosto programje", "igre", "grafične kartice", "procesorji", "pomnilnik", "trdi disk",
        "ssd", "chatgpt", "openai", "dall-e", "strojno učenje", "programiranje", "koda",
        "python", "c++", "javascript", "spletna stran", "računalniška oprema", "tehnologija"
    ]

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
    
def combined_score(link_tag, url, meta_keywords=None, last_accessed=None, keyword_match_count=0):
    bow_priority = score_url_bow(link_tag)         # 0.0 (relevantno) → 1.0 (ne)
    bow_score = bow_priority * 0.6                  # max 0.6

    # Globina URL-ja
    path_depth = urlparse(url).path.count('/')
    depth_score = max(0, 3 - path_depth) * 0.05     # max 0.15

    # Meta ključne besede
    meta_boost = 0

    if meta_keywords:
        keywords = meta_keywords.lower()
        matches = sum(1 for term in slovene_keywords if term in keywords)
        if matches >= 3:
            meta_boost = -0.25
        elif matches >= 1:
            meta_boost = -0.1

    # Svežina
    freshness_boost = 0
    if last_accessed:
        seconds = (datetime.utcnow() - last_accessed).total_seconds()
        if seconds < 3600:
            freshness_boost = -0.1
        elif seconds < 86400:
            freshness_boost = -0.05
            
    # Dodatni boost za poti
    path_boost = 0
    if "/forum" in url:
        path_boost = -0.2
    elif "/clanki" in url:
        path_boost = -0.15
    elif "/isci" in url:
        path_boost = -0.1
        
    # Dodatni boost glede na vsebino strani (če je bila že analizirana)
    content_boost = 0
    if keyword_match_count >= 3:
        content_boost = -0.25
    elif keyword_match_count >= 1:
        content_boost = -0.1

    total = bow_score + depth_score + meta_boost + freshness_boost + path_boost + content_boost

    # DEBUG: Izpis točkovanja za vsak link
    print(f"\n[PRIORITY] URL: {url}")
    print(f"  BoW score:     {bow_score:.4f}")
    print(f"  Depth score:   {depth_score:.4f}")
    print(f"  Meta boost:    {meta_boost:.4f}")
    print(f"  Freshness:     {freshness_boost:.4f}")
    print(f"  Content boost: {content_boost:.4f}")
    print(f"  Final priority:{total:.4f}")

    return float(max(0.0, round(total, 4)))

def content_keyword_match(html, keyword_list):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        matches = sum(1 for term in keyword_list if term in text)
        return matches
    except Exception as e:
        print(f"[ERROR] Failed keyword match in content: {e}")
        return 0