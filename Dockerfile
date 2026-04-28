# =============================================================================
# Image Docker custom AniData Airflow
# =============================================================================
# Étend l'image officielle Apache Airflow 2.x avec :
#   - le package anidata_scraper (BeautifulSoup + requests)
#   - elasticsearch-py (pour etl_dag)
#   - les DAGs (scraper_dag, etl_dag)
#
# Buildée et publiée automatiquement par .github/workflows/ci-cd.yml
# à chaque merge sur main.
# =============================================================================

FROM apache/airflow:2.10.4-python3.10

LABEL org.opencontainers.image.title="AniData Airflow"
LABEL org.opencontainers.image.description="Airflow custom pour AniData Lab — scraper + DAGs"
LABEL org.opencontainers.image.licenses="MIT"

USER airflow

# --- Dépendances Python -------------------------------------------------------
# On copie d'abord uniquement requirements.txt pour profiter du cache Docker :
# tant qu'il n'a pas changé, cette couche n'est pas reconstruite.
COPY --chown=airflow:root anidata-scraper/requirements.txt /tmp/scraper-requirements.txt
RUN pip install --no-cache-dir -r /tmp/scraper-requirements.txt \
    && pip install --no-cache-dir "elasticsearch>=8.0,<9.0"

# --- Package scraper ----------------------------------------------------------
# On copie le pyproject.toml + le code source, puis on installe le package.
# Ainsi `from anidata_scraper import scrape_to_file` fonctionne dans les DAGs.
COPY --chown=airflow:root anidata-scraper/pyproject.toml /opt/airflow/scraper/pyproject.toml
COPY --chown=airflow:root anidata-scraper/anidata_scraper/ /opt/airflow/scraper/anidata_scraper/
RUN pip install --no-cache-dir /opt/airflow/scraper/

# --- DAGs ---------------------------------------------------------------------
COPY --chown=airflow:root dags/ /opt/airflow/dags/

# --- Dossier de données -------------------------------------------------------
# Volume monté dans docker-compose pour persister les fichiers JSON bruts.
RUN mkdir -p /opt/airflow/data/raw

# Vérification rapide : le package s'importe correctement
RUN python -c "import anidata_scraper; print('AniData Scraper OK')"
