"""
DAG stats_dag — Lit le dernier JSON scrapé et affiche les statistiques.

Déclenché manuellement ou après scraper_dag.
Visible dans Airflow dès que le fichier est présent dans ./dags/ (volume monté).

Tâches :
    lire_stats → afficher_resume
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
    "retries": 0,
    "email_on_failure": False,
}


def lire_stats(**context) -> dict:
    """Lit le JSON le plus récent et pousse les stats dans XCom."""
    output_dir = Variable.get("SCRAPER_OUTPUT_DIR", default_var="/opt/airflow/data/raw")
    dossier = Path(output_dir)

    fichiers = sorted(dossier.glob("anime_*.json"), reverse=True)
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier anime_*.json dans {output_dir}")

    fichier = fichiers[0]
    logger.info("Fichier analysé : %s", fichier)

    data = json.loads(fichier.read_text(encoding="utf-8"))
    stats = data.get("stats", {})
    stats["fichier"] = fichier.name
    stats["scraped_at"] = data.get("scraped_at", "inconnu")

    context["ti"].xcom_push(key="stats", value=stats)
    return stats


def afficher_resume(**context) -> None:
    """Affiche un résumé lisible dans les logs Airflow."""
    stats = context["ti"].xcom_pull(task_ids="lire_stats", key="stats")

    logger.info("=" * 50)
    logger.info("RÉSUMÉ DU SCRAPING")
    logger.info("=" * 50)
    logger.info("Fichier      : %s", stats.get("fichier"))
    logger.info("Scrapé le    : %s", stats.get("scraped_at"))
    logger.info("Animes       : %d", stats.get("animes_count", 0))
    logger.info("News         : %d", stats.get("news_count", 0))
    logger.info("Sans score   : %d", stats.get("missing_scores", 0))
    logger.info("Sans studio  : %d", stats.get("missing_studios", 0))
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
