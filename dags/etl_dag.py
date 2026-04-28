"""
DAG etl_dag — Lit le JSON brut et indexe les données dans Elasticsearch.

Chaîne des tâches :
    charger_dans_elasticsearch

Ce DAG est déclenché par scraper_dag via TriggerDagRunOperator.
Il reçoit le chemin du fichier JSON dans dag_run.conf["filepath"].

Si déclenché manuellement (sans conf), il prend le fichier le plus récent
dans le dossier /opt/airflow/data/raw/.
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

# ── Paramètres par défaut ─────────────────────────────────────────────────────
default_args = {
    "owner": "anidata",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# ── Fonctions ETL ─────────────────────────────────────────────────────────────

def _trouver_fichier_recent(output_dir: str) -> str:
    """Renvoie le fichier anime_*.json le plus récent du répertoire."""
    dossier = Path(output_dir)
    fichiers = sorted(dossier.glob("anime_*.json"), reverse=True)
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier anime_*.json trouvé dans {output_dir}")
    logger.info("Fichier le plus récent : %s", fichiers[0])
    return str(fichiers[0])


def _preparer_documents(animes: list[dict], scraped_at: str) -> list[dict]:
    """Transforme la liste brute en documents prêts pour Elasticsearch."""
    docs = []
    for anime in animes:
        doc = {
            "_index": "animes",
            "_id": anime["id"],
            "_source": {
                "id": anime["id"],
                "title_en": anime.get("title_en"),
                "title_jp": anime.get("title_jp"),
                "year": anime.get("year"),
                "studio": anime.get("studio"),
                "score": anime.get("score"),
                "genres": anime.get("genres", []),
                "type": anime.get("type"),
                "episodes": anime.get("episodes"),
                "status": anime.get("status"),
                "synopsis": anime.get("synopsis"),
                "source_url": anime.get("detail_url"),
                "scraped_at": scraped_at,
            },
        }
        docs.append(doc)
    return docs


def charger_dans_elasticsearch(**context) -> None:
    """Lit le JSON brut, transforme et indexe en masse dans Elasticsearch."""
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk

    # ── Récupération du chemin du fichier ────────────────────────────────────
    # Priorité 1 : conf transmis par scraper_dag via TriggerDagRunOperator
    # Priorité 2 : fichier le plus récent (déclenchement manuel)
    dag_run = context["dag_run"]
    output_dir = Variable.get("SCRAPER_OUTPUT_DIR", default_var="/opt/airflow/data/raw")

    if dag_run.conf and dag_run.conf.get("filepath"):
        filepath = dag_run.conf["filepath"]
        logger.info("Fichier reçu via conf : %s", filepath)
    else:
        logger.warning("Aucun filepath dans conf — recherche du fichier le plus récent")
        filepath = _trouver_fichier_recent(output_dir)

    # ── Lecture du JSON ───────────────────────────────────────────────────────
    data = json.loads(Path(filepath).read_text(encoding="utf-8"))
    animes = data.get("animes", [])
    scraped_at = data.get("scraped_at", datetime.utcnow().isoformat())

    logger.info("Fichier lu : %d animes à indexer", len(animes))

    # ── Connexion à Elasticsearch ─────────────────────────────────────────────
    es_url = Variable.get("ELASTICSEARCH_URL", default_var="http://elasticsearch:9200")
    es = Elasticsearch(es_url)

    if not es.ping():
        raise ConnectionError(f"Impossible de joindre Elasticsearch sur {es_url}")

    # ── Indexation en masse ───────────────────────────────────────────────────
    documents = _preparer_documents(animes, scraped_at)
    succes, erreurs = bulk(es, documents, raise_on_error=False)

    logger.info("Indexation terminée : %d documents OK, %d erreurs", succes, len(erreurs))

    if erreurs:
        for err in erreurs[:5]:  # log des 5 premières erreurs seulement
            logger.error("Erreur d'indexation : %s", err)

    # Résumé visible dans les logs Airflow
    context["ti"].log.info(
        "ETL terminé — %d animes indexés dans Elasticsearch (index : animes)",
        succes,
    )


# ── Définition du DAG ─────────────────────────────────────────────────────────

with DAG(
    dag_id="etl_dag",
    description="Charge les données scrapées dans Elasticsearch",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval=None,  # déclenché uniquement par scraper_dag
    catchup=False,
    tags=["etl", "elasticsearch", "anidata"],
) as dag:

    charger = PythonOperator(
        task_id="charger_dans_elasticsearch",
        python_callable=charger_dans_elasticsearch,
    )
