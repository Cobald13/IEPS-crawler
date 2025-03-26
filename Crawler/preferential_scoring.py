from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import urlparse
from datetime import datetime

# Ključna opisna fraza
TARGET_DESCRIPTION = "slo-tech forum razprave članki trendi umetna inteligenca strojna oprema programska oprema"

# Slovenske stop besede
slovene_stop_words = [
    "in", "ali", "je", "se", "za", "na", "da", "s", "so", "kot", "ki", "po", "z", "ob"
]
vectorizer = CountVectorizer(stop_words=slovene_stop_words)
vectorizer.fit([TARGET_DESCRIPTION])

# Seznam ključnih besed
slovene_keywords = [
    "računalništvo", "strojna oprema", "programska oprema", "operacijski sistem", "varnost",
    "hekanje", "splet", "umetna inteligenca", "robotika", "algoritmi", "računalniška omrežja",
    "internet", "novice", "članki", "trendi", "diskusija", "forum", "debata", "računalniki",
    "mobilne naprave", "pametni telefoni", "android", "linux", "windows", "open source",
    "prosto programje", "igre", "grafične kartice", "procesorji", "pomnilnik", "trdi disk",
    "ssd", "chatgpt", "openai", "dall-e", "strojno učenje", "programiranje", "koda",
    "python", "c++", "javascript", "spletna stran", "računalniška oprema", "tehnologija"
]

# BoW ocena iz okoliškega teksta
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
        priority = max(0.0, min(1.0, priority))  # clamp
        return priority
    except Exception as e:
        print(f"[BoW ERROR] {e}")
        return 1.0

# Glavna kombinirana ocena
def combined_score(link_tag, url, meta_keywords=None, last_accessed=None, keyword_match_count=0):
    bow_priority = score_url_bow(link_tag)
    bow_score = min(0.6, bow_priority * 0.6) * 0    # trenutno ne uporabljamo BoW

    # Globina URL-ja
    path_depth = urlparse(url).path.count('/')
    depth_score = max(0, 3 - path_depth) * 0.05

    # Meta tag boost
    meta_boost = 0
    if meta_keywords:
        keywords = meta_keywords.lower()
        matches = sum(1 for term in slovene_keywords if term in keywords)
        if matches >= 3:
            meta_boost = -0.5
        elif matches >= 1:
            meta_boost = -0.25

    # Svežina
    freshness_boost = 0
    if last_accessed:
        seconds = (datetime.utcnow() - last_accessed).total_seconds()
        if seconds < 3600:
            freshness_boost = -0.1
        elif seconds < 86400:
            freshness_boost = -0.05

    # URL poti
    path_boost = 0
    if "/forum" in url:
        path_boost = -0.2
    elif "/clanki" in url:
        path_boost = -0.15
    elif "/isci" in url:
        path_boost = -0.1

    # Vsebinsko ujemanje
    content_boost = 0
    if keyword_match_count >= 5:
        content_boost = -0.4
    elif keyword_match_count >= 2:
        content_boost = -0.2

    # Domeno ali URL, ki vsebuje "slo-tech"
    domain_boost = 0
    if "slo-tech" in url:
        domain_boost = -0.3
    else:
        domain_boost = 0.1  # - za tuje domene

    total = depth_score + meta_boost + freshness_boost + path_boost + content_boost + domain_boost # + bow_score

    # Debug izpis
    print(f"\n[PRIORITY] URL: {url}")
    print(f"  BoW score:     {bow_score:.4f}")
    print(f"  Depth score:   {depth_score:.4f}")
    print(f"  Meta boost:    {meta_boost:.4f}")
    print(f"  Freshness:     {freshness_boost:.4f}")
    print(f"  Path boost:    {path_boost:.4f}")
    print(f"  Content boost: {content_boost:.4f}")
    print(f"  Domain boost:  {domain_boost:.4f}")
    print(f"  Final priority:{total:.4f}")

    return float(max(0.0, round(total, 4)))

# Vsebinsko štetje ključnih besed
def content_keyword_match(html, keyword_list):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text().lower()
        matches = sum(1 for term in keyword_list if term in text)
        return matches
    except Exception as e:
        print(f"[ERROR] Failed keyword match in content: {e}")
        return 0
