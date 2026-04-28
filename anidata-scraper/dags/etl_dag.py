"""
DAG etl_dag — AniData Lab
Lit le JSON produit par scraper_dag,
transforme les données et les indexe dans Elasticsearch.
"""
from __future__ import annotations

import glob
import json
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor

# ===========================================================
# Configuration du DAG
# ===========================================================
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="etl_dag",
    description="Charge les données scrapées dans Elasticsearch",
    default_args=default_args,
    start_date=datetime(2026, 4, 27),
    schedule_interval="@daily",
    catchup=False,
    tags=["etl", "elasticsearch", "anidata"],
) as dag:

    def load_to_elasticsearch():
        """Lit le JSON le plus récent et l'indexe dans Elasticsearch."""
        from elasticsearch import Elasticsearch

        # Connexion Elasticsearch
        es = Elasticsearch("http://elasticsearch:9200")

        # Trouve le fichier JSON le plus récent
        files = glob.glob("/opt/airflow/data/raw/anime_*.json")
        if not files:
            raise FileNotFoundError("Aucun fichier JSON trouvé dans data/raw/")

        latest_file = max(files, key=os.path.getctime)
        print(f"📂 Chargement du fichier : {latest_file}")

        with open(latest_file, encoding="utf-8") as f:
            animes = json.load(f)

        # Indexation dans Elasticsearch
        success = 0
        for anime in animes:
            es.index(
                index="animes",
                id=anime["id"],
                document={
                    "titre": anime["titre"],
                    "annee": anime["annee"],
                    "studio": anime["studio"],
                    "score": anime["score"],
                    "genres": anime["genres"],
                    "indexed_at": datetime.now().isoformat(),
                },
            )
            success += 1

        print(f"✅ {success} animés indexés dans Elasticsearch")
        return success

    etl_task = PythonOperator(
        task_id="load_to_elasticsearch",
        python_callable=load_to_elasticsearch,
    )