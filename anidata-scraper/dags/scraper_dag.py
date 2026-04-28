"""
DAG scraper_dag — AniData Lab
Lance le scraper BeautifulSoup sur le mock-site nginx
et écrit le résultat dans /opt/airflow/data/raw/
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# ===========================================================
# Configuration du DAG
# ===========================================================
default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="scraper_dag",
    description="Scrape le mock-site AniDex et sauvegarde en JSON",
    default_args=default_args,
    start_date=datetime(2026, 4, 27),
    schedule_interval="@daily",
    catchup=False,
    tags=["scraping", "anidata"],
) as dag:

    def run_scraper():
        """Lance le scraper et sauvegarde les données."""
        from anidata_scraper.scraper import save, scrape_all

        print("🚀 Démarrage du scraper AniDex...")
        animes = scrape_all(base_url="http://anidata-mock-site:80")
        filepath = save(animes, output_dir="/opt/airflow/data/raw")
        print(f"✅ {len(animes)} animés sauvegardés dans : {filepath}")
        return filepath

    scrape_task = PythonOperator(
        task_id="scrape_anidex",
        python_callable=run_scraper,
    )