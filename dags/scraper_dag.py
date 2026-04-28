"""
DAG scraper_dag — Lance le scraper AniDex et déclenche etl_dag puis stats_dag.

Chaîne des tâches :
    scraping → declencher_etl → declencher_stats

- scraping          : appelle scrape_to_file(), écrit un JSON dans /opt/airflow/data/raw/
                      et pousse le chemin du fichier via XCom.
- declencher_etl    : déclenche etl_dag en lui transmettant le chemin du fichier
                      via le paramètre conf.
- declencher_stats  : déclenche stats_dag pour afficher les statistiques du scraping.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# ── Paramètres par défaut appliqués à toutes les tâches ──────────────────────
default_args = {
    "owner": "anidata",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

# ── Fonction appelée par le PythonOperator ────────────────────────────────────

def lancer_scraping(**context) -> str:
    """Scrape le mock-site et écrit le résultat en JSON.

    La valeur de retour est automatiquement poussée dans XCom par Airflow
    et récupérée par TriggerDagRunOperator pour transmettre le chemin au DAG ETL.
    """
    from anidata_scraper.scraper import scrape_to_file

    # Variable Airflow configurable depuis l'UI (Settings > Variables)
    # Valeur par défaut : nom du service Docker dans docker-compose
    base_url = Variable.get("MOCK_SITE_URL", default_var="http://mock-site")
    output_dir = Variable.get("SCRAPER_OUTPUT_DIR", default_var="/opt/airflow/data/raw")

    filepath = scrape_to_file(
        output_dir=output_dir,
        base_url=base_url,
        enrich=True,
    )

    context["ti"].log.info("Fichier produit : %s", filepath)
    return filepath  # → XCom automatique


# ── Définition du DAG ─────────────────────────────────────────────────────────

with DAG(
    dag_id="scraper_dag",
    description="Scrape le mock-site AniDex et déclenche le pipeline ETL",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["scraping", "anidata"],
) as dag:

    scraping = PythonOperator(
        task_id="scraping",
        python_callable=lancer_scraping,
    )

    # Jinja template : récupère le chemin du fichier depuis XCom de la tâche précédente
    declencher_etl = TriggerDagRunOperator(
        task_id="declencher_etl",
        trigger_dag_id="etl_dag",
        conf={"filepath": "{{ ti.xcom_pull(task_ids='scraping') }}"},
        wait_for_completion=False,
    )

    declencher_stats = TriggerDagRunOperator(
        task_id="declencher_stats",
        trigger_dag_id="stats_dag",
        wait_for_completion=False,
    )

    scraping >> declencher_etl >> declencher_stats
