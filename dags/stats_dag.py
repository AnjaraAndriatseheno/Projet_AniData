"""
DAG stats_dag — Lit le dernier JSON scrapé et affiche des statistiques.

Chaîne des tâches :
    lire_stats → afficher_resume

- lire_stats      : trouve le fichier anime_*.json le plus récent,
                    calcule les stats et les pousse dans XCom.
- afficher_resume : affiche un résumé lisible dans les logs Airflow.

Ce DAG est déclenché automatiquement par scraper_dag après chaque scraping.
Il peut aussi être lancé manuellement depuis l'interface Airflow.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator

logger = logging.getLogger(__name__)

default_args = {
    "owner": "anidata",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}


def lire_stats(**context) -> dict:
    """Lit le fichier JSON le plus récent et calcule les statistiques."""
    output_dir = Variable.get("SCRAPER_OUTPUT_DIR", default_var="/opt/airflow/data/raw")
    dossier = Path(output_dir)
    fichiers = sorted(dossier.glob("anime_*.json"), reverse=True)

    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier anime_*.json dans {output_dir}")

    fichier = fichiers[0]
    logger.info("Fichier analysé : %s", fichier)

    data = json.loads(fichier.read_text(encoding="utf-8"))
    animes = data.get("animes", [])
    scraped_at = data.get("scraped_at", "inconnu")

    stats = {
        "fichier": fichier.name,
        "scraped_at": scraped_at,
        "animes_count": len(animes),
        "missing_scores": sum(1 for a in animes if not a.get("score")),
        "missing_studios": sum(1 for a in animes if not a.get("studio")),
    }

    context["ti"].xcom_push(key="stats", value=stats)
    return stats


def afficher_resume(**context) -> None:
    """Affiche un résumé lisible dans les logs Airflow."""
    stats = context["ti"].xcom_pull(task_ids="lire_stats", key="stats")

    logger.info("=" * 50)
    logger.info("Statistiques du dernier scraping")
    logger.info("=" * 50)
    logger.info("Fichier      : %s", stats["fichier"])
    logger.info("Scrapé le    : %s", stats["scraped_at"])
    logger.info("Animes       : %d", stats["animes_count"])
    logger.info("Sans score   : %d", stats["missing_scores"])
    logger.info("Sans studio  : %d", stats["missing_studios"])
    logger.info("=" * 50)


with DAG(
    dag_id="stats_dag",
    description="Affiche les statistiques du dernier scraping",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["stats", "monitoring", "anidata"],
) as dag:

    lire = PythonOperator(
        task_id="lire_stats",
        python_callable=lire_stats,
    )

    afficher = PythonOperator(
        task_id="afficher_resume",
        python_callable=afficher_resume,
    )

    lire >> afficher
