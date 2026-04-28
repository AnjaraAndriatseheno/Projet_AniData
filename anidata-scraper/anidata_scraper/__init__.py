"""AniData Lab scraper package."""
<<<<<<< HEAD
from anidata_scraper.scraper import (
    AniDexScraper,
    Anime,
    NewsArticle,
    scrape_to_file,
)

__all__ = ["AniDexScraper", "Anime", "NewsArticle", "scrape_to_file"]
=======
from anidata_scraper.scraper import fetch, parse, save, scrape_all

__all__ = ["fetch", "parse", "save", "scrape_all"]
>>>>>>> 47d4f198d372fe6a0f177913f689f6f835691516
__version__ = "1.0.0"
