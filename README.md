<<<<<<< HEAD
# AniData Lab — DevOps & CI/CD

Pipeline de données automatisée pour le studio **Sakura Analytics**.  
À chaque `git push`, le code est testé, une image Docker est publiée, et les données anime sont scrapées et indexées dans Elasticsearch.

---

## Architecture

```
Dev (VS Code)
      │ git push
      ▼
GitHub (repo)
      │ déclenche
      ▼
GitHub Actions
      ├── Lint (ruff)
      ├── Tests (pytest · Python 3.10 & 3.11)
      └── Build + Push image Docker → GHCR
                    │
                    ▼
         Airflow (Docker Compose)
                    │ pull de la nouvelle image
                    ▼
           DAG : scraper_dag
                    │ scrape mock-site nginx avec BeautifulSoup
                    │ écrit /opt/airflow/data/raw/anime_YYYYMMDD.json
                    │ TriggerDagRunOperator
                    ▼
           DAG : etl_dag
                    │ lit le JSON → transforme → bulk insert
                    ▼
           Elasticsearch (index : animes)
                    │
                    ▼
           Grafana (dashboard auto-refresh)
```

---

## Stack technique

| Composant | Technologie |
|---|---|
| Gestion de versions | Git, GitHub, GitFlow light |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |
| Qualité du code | ruff (lint), pytest (tests unitaires) |
| Scraping | Python 3.10, requests, BeautifulSoup4 |
| Site cible | nginx (mock-site fourni) |
| Conteneurisation | Docker, Docker Compose |
| Orchestration | Apache Airflow 2.10 |
| Stockage | Elasticsearch 8.x |
| Visualisation | Grafana 10.x |

---

## Structure du projet

```
Projet_AniData/
├── .github/
│   └── workflows/
│       ├── blank.yml       # CI : lint + tests sur branche dev
│       └── ci-cd.yml       # CI/CD complet sur branche main (+ build Docker)
├── anidata-scraper/
│   ├── anidata_scraper/
│   │   ├── __init__.py
│   │   └── scraper.py      # Scraper BeautifulSoup (fetch, parse, retry)
│   ├── tests/
│   │   ├── fixtures.py
│   │   └── test_scraper.py # 12 tests unitaires
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── requirements-dev.txt
├── dags/
│   ├── scraper_dag.py      # DAG scraping quotidien → déclenche etl_dag
│   └── etl_dag.py          # DAG ETL → indexation Elasticsearch
├── mock-site/
│   └── site/               # Site nginx statique (catalogue anime)
├── Dockerfile              # Image Airflow custom (scraper + DAGs inclus)
├── docker-compose.yml      # Stack complète locale
└── README.md
```

---

## Installation et lancement local

### Prérequis

- Docker Desktop installé et démarré
- Git
- Python 3.10+ (pour les tests locaux)

### 1. Cloner le repo

```bash
git clone git@github.com:<ton-org>/Projet_AniData.git
cd Projet_AniData
```

### 2. Builder l'image Docker

```bash
docker build -t anidata-airflow:local .
```

### 3. Initialiser Airflow (première fois uniquement)

```bash
docker compose up airflow-init
```

Attendre le message `Admin user created` puis arrêter avec `Ctrl+C`.

### 4. Lancer toute la stack

```bash
docker compose up -d
```

### 5. Vérifier que tout tourne

```bash
docker compose ps
```

### 6. Accéder aux interfaces

| Service | URL | Identifiants |
|---|---|---|
| Airflow | http://localhost:8080 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Elasticsearch | http://localhost:9200 | — |
| Mock-site | http://localhost:8088 | — |

---

## Tester le pipeline manuellement

1. Ouvrir Airflow sur http://localhost:8080
2. Activer le DAG `scraper_dag`
3. Cliquer sur **Trigger DAG** (bouton ▶)
4. Observer les tâches : `scraping` → `declencher_etl`
5. Le DAG `etl_dag` se déclenche automatiquement
6. Vérifier les données dans Elasticsearch :

```bash
curl http://localhost:9200/animes/_count
```

7. Ouvrir Grafana sur http://localhost:3000 pour voir les dashboards mis à jour

---

## Chaîne CI/CD

### Stratégie de branches (GitFlow light)

```
feature/*  →  dev   →  main
              ↑           ↑
           CI only    CI/CD complet
         (blank.yml)  (ci-cd.yml)
```

### Ce qui se passe à chaque push sur `main`

1. **Lint** : `ruff check` vérifie le style du code
2. **Tests** : `pytest` sur Python 3.10 et 3.11 en parallèle
3. **Build** : construction de l'image Docker Airflow custom
4. **Push** : publication sur GHCR avec 3 tags :
   - `latest` (dernier build de main)
   - `sha-abc1234` (SHA court du commit)
   - `v1.2.3` (si un tag Git existe)

### Utiliser l'image GHCR en production

Remplacer l'image locale par l'image publiée :

```bash
AIRFLOW_IMAGE_NAME=ghcr.io/<org>/<repo>-airflow:latest docker compose up -d
```

### Variables Airflow configurables

Depuis l'UI Airflow → **Admin > Variables** :

| Variable | Valeur par défaut | Rôle |
|---|---|---|
| `MOCK_SITE_URL` | `http://mock-site` | URL du site à scraper |
| `SCRAPER_OUTPUT_DIR` | `/opt/airflow/data/raw` | Dossier des fichiers JSON |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | URL d'Elasticsearch |

---

## Lancer les tests localement

```bash
cd anidata-scraper
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## Arrêter la stack

```bash
docker compose down
```

Pour supprimer aussi les volumes (données Elasticsearch, Grafana) :

```bash
docker compose down -v
```
=======
# Projet_AniData
>>>>>>> 47d4f198d372fe6a0f177913f689f6f835691516
