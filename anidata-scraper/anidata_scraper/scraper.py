import json
import os
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ===========================================================
# Scraper AniDex — AniData Lab
# Cible : mock-site nginx local (http://localhost:8088)
# Scrape les 4 pages du catalogue et sauvegarde en JSON
# ===========================================================

BASE_URL = "http://localhost:8088"
PAGES = [
    "/animes/page-1.html",
    "/animes/page-2.html",
    "/animes/page-3.html",
    "/animes/page-4.html",
]
OUTPUT_DIR = "data/raw"


# -----------------------------------------------------------
# FONCTION 1 : fetch — télécharge le HTML d'une page
# -----------------------------------------------------------
def fetch(url: str) -> str:
    """Télécharge le contenu HTML d'une URL et le retourne."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


# -----------------------------------------------------------
# FONCTION 2 : parse — extrait les animés d'une page HTML
# -----------------------------------------------------------
def parse(html: str) -> list[dict]:
    """Parse le HTML et retourne une liste d'animés."""
    soup = BeautifulSoup(html, "html.parser")
    animes = []

    for card in soup.find_all("article", class_="anime-card"):
        # Titre
        titre_tag = card.find("h3")
        titre = titre_tag.get_text(strip=True) if titre_tag else "N/A"

        # Année — deux formats possibles dans le HTML
        year_tag = card.find("span", class_="year")
        if year_tag and year_tag.get("data-year"):
            annee = year_tag["data-year"]
        elif year_tag:
            annee = year_tag.get_text(strip=True).replace("Année : ", "")
        else:
            annee = "N/A"

        # Studio — deux formats possibles dans le HTML
        studio_tag = card.find("span", class_="studio")
        if studio_tag and studio_tag.get("data-studio"):
            studio = studio_tag["data-studio"]
        elif studio_tag:
            studio = studio_tag.get_text(strip=True).replace("🎬 ", "")
        else:
            studio = "N/A"

        # Score — gère les valeurs N/A
        score_tag = card.find("span", class_="score")
        if score_tag and score_tag.get("data-score"):
            raw_score = score_tag["data-score"]
            score = float(raw_score) if raw_score != "N/A" else None
        else:
            score = None

        # Genres
        genres = [g.get_text(strip=True) for g in card.find_all("span", class_="genre-tag")]

        # ID
        anime_id = card.get("data-anime-id", "N/A")

        animes.append({
            "id": anime_id,
            "titre": titre,
            "annee": annee,
            "studio": studio,
            "score": score,
            "genres": genres,
        })

    return animes


# -----------------------------------------------------------
# FONCTION 3 : save — sauvegarde les données en JSON
# -----------------------------------------------------------
def save(animes: list[dict], output_dir: str = OUTPUT_DIR) -> str:
    """Sauvegarde la liste d'animés dans un fichier JSON horodaté."""
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime("%Y%m%d")
    filepath = os.path.join(output_dir, f"anime_{date_str}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(animes, f, ensure_ascii=False, indent=2)

    return filepath


# -----------------------------------------------------------
# MAIN — scrape toutes les pages et sauvegarde
# -----------------------------------------------------------
def scrape_all(base_url: str = BASE_URL, pages: list = PAGES) -> list[dict]:
    """Scrape toutes les pages du catalogue et retourne tous les animés."""
    tous_les_animes = []

    for page in pages:
        url = base_url + page
        print(f"📥 Scraping : {url}")
        html = fetch(url)
        animes = parse(html)
        print(f"   → {len(animes)} animés trouvés")
        tous_les_animes.extend(animes)

    # Dédoublonnage par ID
    seen = set()
    animes_uniques = []
    for anime in tous_les_animes:
        if anime["id"] not in seen:
            seen.add(anime["id"])
            animes_uniques.append(anime)

    return animes_uniques


if __name__ == "__main__":
    print("🚀 Démarrage du scraper AniDex...")
    animes = scrape_all()
    filepath = save(animes)
    print(f"\n✅ {len(animes)} animés sauvegardés dans : {filepath}")