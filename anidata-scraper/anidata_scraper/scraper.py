"""Tests unitaires du scraper AniDex.

On teste la logique de parsing sans appels HTTP réels,
en utilisant des fragments HTML fixes.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from anidata_scraper.scraper import fetch, parse, save, scrape_all

# ===========================================================
# FIXTURES HTML — fragments de pages pour les tests
# ===========================================================

CARD_NORMAL = """
<article class="anime-card" data-anime-id="1">
  <h3><a href="/anime/attack-on-titan.html">Attack on Titan</a></h3>
  <div class="jp-title">進撃の巨人</div>
  <div class="meta">
    <span class="year" data-year="2013">📅 2013</span>
    <span class="studio" data-studio="Wit Studio">🎬 Wit Studio</span>
    <span class="score" data-score="9.0">★ 9.0</span>
  </div>
  <div class="genres">
    <span class="genre-tag">Action</span>
    <span class="genre-tag">Drama</span>
    <span class="genre-tag">Fantasy</span>
  </div>
</article>
"""

CARD_NA_SCORE = """
<article class="anime-card" data-anime-id="2">
  <h3><a href="/anime/demon-slayer.html">Demon Slayer</a></h3>
  <div class="meta">
    <span class="year" data-year="2019">📅 2019</span>
    <span class="studio" data-studio="Ufotable">🎬 Ufotable</span>
    <span class="score" data-score="N/A">★ N/A</span>
  </div>
  <div class="genres">
    <span class="genre-tag">Action</span>
  </div>
</article>
"""

CARD_VARIANT = """
<article class="anime-card" data-anime-id="17">
  <h3><a href="/anime/hunter-x-hunter.html">Hunter x Hunter (2011)</a></h3>
  <p class="year">Année : 2011</p>
  <span class="studio" data-studio="Madhouse">🎬 Madhouse</span>
  <span class="score" data-score="9.0">★ 9.0</span>
  <div class="genres">
    <span class="genre-tag">Action</span>
    <span class="genre-tag">Adventure</span>
  </div>
</article>
"""

CATALOG_PAGE = f"""
<html><body>
{CARD_NORMAL}
{CARD_NA_SCORE}
{CARD_VARIANT}
</body></html>
"""


# ===========================================================
# TESTS DE parse()
# ===========================================================

class TestParse:

    def test_parse_carte_normale(self):
        """Une carte normale doit retourner tous les champs."""
        animes = parse(CARD_NORMAL)
        assert len(animes) == 1
        anime = animes[0]
        assert anime["id"] == "1"
        assert anime["titre"] == "Attack on Titan"
        assert anime["annee"] == "2013"
        assert anime["studio"] == "Wit Studio"
        assert anime["score"] == 9.0
        assert anime["genres"] == ["Action", "Drama", "Fantasy"]

    def test_parse_score_na(self):
        """Un score N/A doit produire score=None, pas une exception."""
        animes = parse(CARD_NA_SCORE)
        assert len(animes) == 1
        assert animes[0]["score"] is None
        assert animes[0]["titre"] == "Demon Slayer"

    def test_parse_structure_variante(self):
        """La structure sans wrapper .meta doit aussi fonctionner."""
        animes = parse(CARD_VARIANT)
        assert len(animes) == 1
        anime = animes[0]
        assert anime["id"] == "17"
        assert anime["titre"] == "Hunter x Hunter (2011)"
        assert anime["studio"] == "Madhouse"
        assert anime["score"] == 9.0

    def test_parse_page_complete(self):
        """Une page avec 3 cartes doit retourner 3 animés."""
        animes = parse(CATALOG_PAGE)
        assert len(animes) == 3
        titres = [a["titre"] for a in animes]
        assert "Attack on Titan" in titres
        assert "Demon Slayer" in titres
        assert "Hunter x Hunter (2011)" in titres

    def test_parse_page_vide(self):
        """Une page sans carte doit retourner une liste vide."""
        animes = parse("<html><body><p>rien</p></body></html>")
        assert animes == []


# ===========================================================
# TESTS DE fetch()
# ===========================================================

class TestFetch:

    def test_fetch_retourne_html(self):
        """fetch() doit retourner le contenu HTML de la page."""
        fake_response = MagicMock()
        fake_response.text = "<html><body>ok</body></html>"
        fake_response.raise_for_status = MagicMock()

        with patch("anidata_scraper.scraper.requests.get", return_value=fake_response):
            result = fetch("http://localhost:8088/animes/page-1.html")

        assert result == "<html><body>ok</body></html>"

    def test_fetch_leve_exception_sur_404(self):
        """fetch() doit lever une exception si la page n'existe pas."""
        import requests

        fake_response = MagicMock()
        fake_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("anidata_scraper.scraper.requests.get", return_value=fake_response):
            with pytest.raises(requests.HTTPError):
                fetch("http://localhost:8088/page-inexistante.html")


# ===========================================================
# TESTS DE save()
# ===========================================================

class TestSave:

    def test_save_cree_fichier_json(self, tmp_path):
        """save() doit créer un fichier JSON dans le dossier indiqué."""
        animes = [
            {"id": "1", "titre": "Attack on Titan", "score": 9.0, "genres": ["Action"]}
        ]
        filepath = save(animes, output_dir=str(tmp_path))

        assert Path(filepath).exists()
        assert Path(filepath).name.startswith("anime_")
        assert Path(filepath).name.endswith(".json")

    def test_save_contenu_correct(self, tmp_path):
        """Le JSON sauvegardé doit contenir les bonnes données."""
        animes = [
            {"id": "1", "titre": "Test Anime", "score": 8.5, "genres": ["Drama"]}
        ]
        filepath = save(animes, output_dir=str(tmp_path))
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))

        assert len(data) == 1
        assert data[0]["titre"] == "Test Anime"
        assert data[0]["score"] == 8.5

    def test_save_cree_dossier_si_absent(self, tmp_path):
        """save() doit créer le dossier output s'il n'existe pas."""
        nouveau_dossier = str(tmp_path / "nouveau" / "dossier")
        animes = [{"id": "1", "titre": "X"}]
        filepath = save(animes, output_dir=nouveau_dossier)

        assert Path(filepath).exists()


# ===========================================================
# TESTS DE scrape_all()
# ===========================================================

class TestScrapeAll:

    def test_scrape_all_dedoublonne(self):
        """scrape_all() ne doit pas retourner deux fois le même animé."""
        html_avec_doublons = CARD_NORMAL * 2  # même carte deux fois

        with patch("anidata_scraper.scraper.fetch", return_value=html_avec_doublons):
            animes = scrape_all(
                base_url="http://mock",
                pages=["/page-1.html", "/page-2.html"]
            )

        ids = [a["id"] for a in animes]
        assert len(ids) == len(set(ids))

    def test_scrape_all_combine_pages(self):
        """scrape_all() doit combiner les animés de toutes les pages."""
        with patch("anidata_scraper.scraper.fetch", return_value=CATALOG_PAGE):
            animes = scrape_all(
                base_url="http://mock",
                pages=["/page-1.html", "/page-2.html"]
            )

        assert len(animes) == 3
