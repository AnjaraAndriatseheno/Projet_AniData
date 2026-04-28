"""Tests unitaires du scraper AniDex."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from anidata_scraper.scraper import fetch, parse, save, scrape_all

CARD_NORMAL = """
<article class="anime-card" data-anime-id="1">
  <h3><a href="/anime/attack-on-titan.html">Attack on Titan</a></h3>
  <div class="meta">
    <span class="year" data-year="2013">📅 2013</span>
    <span class="studio" data-studio="Wit Studio">🎬 Wit Studio</span>
    <span class="score" data-score="9.0">★ 9.0</span>
  </div>
  <div class="genres">
    <span class="genre-tag">Action</span>
    <span class="genre-tag">Drama</span>
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
  <div class="genres"><span class="genre-tag">Action</span></div>
</article>
"""

CARD_VARIANT = """
<article class="anime-card" data-anime-id="17">
  <h3><a href="/anime/hunter.html">Hunter x Hunter (2011)</a></h3>
  <p class="year">Année : 2011</p>
  <span class="studio" data-studio="Madhouse">🎬 Madhouse</span>
  <span class="score" data-score="9.0">★ 9.0</span>
  <div class="genres"><span class="genre-tag">Action</span></div>
</article>
"""

CATALOG_PAGE = f"<html><body>{CARD_NORMAL}{CARD_NA_SCORE}{CARD_VARIANT}</body></html>"


class TestParse:

    def test_parse_carte_normale(self):
        animes = parse(CARD_NORMAL)
        assert len(animes) == 1
        assert animes[0]["id"] == "1"
        assert animes[0]["titre"] == "Attack on Titan"
        assert animes[0]["annee"] == "2013"
        assert animes[0]["studio"] == "Wit Studio"
        assert animes[0]["score"] == 9.0
        assert "Action" in animes[0]["genres"]

    def test_parse_score_na(self):
        animes = parse(CARD_NA_SCORE)
        assert len(animes) == 1
        assert animes[0]["score"] is None
        assert animes[0]["titre"] == "Demon Slayer"

    def test_parse_structure_variante(self):
        animes = parse(CARD_VARIANT)
        assert len(animes) == 1
        assert animes[0]["id"] == "17"
        assert animes[0]["studio"] == "Madhouse"

    def test_parse_page_complete(self):
        animes = parse(CATALOG_PAGE)
        assert len(animes) == 3

    def test_parse_page_vide(self):
        animes = parse("<html><body><p>rien</p></body></html>")
        assert animes == []


class TestFetch:

    def test_fetch_retourne_html(self):
        fake_response = MagicMock()
        fake_response.text = "<html>ok</html>"
        fake_response.raise_for_status = MagicMock()

        with patch("anidata_scraper.scraper.requests.get", return_value=fake_response):
            result = fetch("http://localhost:8088/animes/page-1.html")

        assert result == "<html>ok</html>"

    def test_fetch_leve_exception_sur_404(self):
        fake_response = MagicMock()
        fake_response.raise_for_status.side_effect = requests.HTTPError("404")

        with patch("anidata_scraper.scraper.requests.get", return_value=fake_response):
            with pytest.raises(requests.HTTPError):
                fetch("http://localhost:8088/inexistant.html")


class TestSave:

    def test_save_cree_fichier_json(self, tmp_path):
        animes = [{"id": "1", "titre": "Attack on Titan", "score": 9.0}]
        filepath = save(animes, output_dir=str(tmp_path))
        assert Path(filepath).exists()
        assert Path(filepath).name.startswith("anime_")

    def test_save_contenu_correct(self, tmp_path):
        animes = [{"id": "1", "titre": "Test", "score": 8.5}]
        filepath = save(animes, output_dir=str(tmp_path))
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
        assert data[0]["titre"] == "Test"

    def test_save_cree_dossier_si_absent(self, tmp_path):
        animes = [{"id": "1", "titre": "X"}]
        filepath = save(animes, output_dir=str(tmp_path / "nouveau"))
        assert Path(filepath).exists()


class TestScrapeAll:

    def test_scrape_all_dedoublonne(self):
        with patch("anidata_scraper.scraper.fetch", return_value=CARD_NORMAL * 2):
            animes = scrape_all(
                base_url="http://mock",
                pages=["/page-1.html", "/page-2.html"],
            )
        ids = [a["id"] for a in animes]
        assert len(ids) == len(set(ids))

    def test_scrape_all_combine_pages(self):
        with patch("anidata_scraper.scraper.fetch", return_value=CATALOG_PAGE):
            animes = scrape_all(
                base_url="http://mock",
                pages=["/page-1.html"],
            )
        assert len(animes) == 3