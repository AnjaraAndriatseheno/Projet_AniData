import io
import os
import zipfile

import requests

# ===========================================================
# Script CI Validator — AniData Scraper
# 1. Vérifie que tous les checks CI sont verts sur GitHub
# 2. Si OK → télécharge le code source (zip) et l'extrait
# Le token est lu depuis la variable d'environnement GITHUB_TOKEN
# ===========================================================

OWNER = "AnjaraAndriatseheno"
REPO = "Projet_AniData"
BRANCH = "dev"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}


# -----------------------------------------------------------
# ÉTAPE 1 : Récupérer le statut des checks CI
# -----------------------------------------------------------
def get_ci_status():
    """Interroge l'API GitHub et retourne True si tous les checks sont OK."""

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{BRANCH}/check-runs"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    check_runs = response.json().get("check_runs", [])

    if not check_runs:
        print("⚠️  Aucun check trouvé sur la branche.")
        return False

    print(f"\n{'Nom du check':<35} {'Statut':<15} {'Résultat'}")
    print("-" * 65)

    all_ok = True
    for check in check_runs:
        name = check["name"]
        status = check["status"]
        conclusion = check.get("conclusion", "en cours...")

        emoji = "✅" if conclusion == "success" else "❌"
        print(f"{name:<35} {status:<15} {emoji}  {conclusion}")

        if conclusion != "success":
            all_ok = False

    print("-" * 65)
    return all_ok


# -----------------------------------------------------------
# ÉTAPE 2 : Télécharger le code source si CI verte
# -----------------------------------------------------------
def download_code():
    """Télécharge le zip du repo sur la branche dev et l'extrait."""

    output_dir = f"{REPO}_{BRANCH}_code"

    print(f"\n📦 Téléchargement du code depuis la branche '{BRANCH}'...")

    url = f"https://api.github.com/repos/{OWNER}/{REPO}/zipball/{BRANCH}"
    response = requests.get(url, headers=HEADERS, stream=True)
    response.raise_for_status()

    # Extraction du zip en mémoire
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(output_dir)

    print(f"✅ Code extrait dans le dossier : '{output_dir}/'")

    # Affiche les fichiers extraits
    print("\n📁 Fichiers récupérés :")
    for root, dirs, files in os.walk(output_dir):
        level = root.replace(output_dir, "").count(os.sep)
        indent = "  " * level
        print(f"{indent}📂 {os.path.basename(root)}/")
        for file in files:
            print(f"{indent}  📄 {file}")


# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------
if __name__ == "__main__":
    if not TOKEN:
        print("❌ GITHUB_TOKEN non défini. Lance : export GITHUB_TOKEN=ghp_...")
        exit(1)

    print("🔍 Vérification de la CI GitHub...")
    print(f"   Repo   : {OWNER}/{REPO}")
    print(f"   Branche: {BRANCH}")

    ci_ok = get_ci_status()

    print("\n" + "=" * 65)
    if ci_ok:
        print("✅ CI OK — Tous les checks sont passés !")
        download_code()
    else:
        print("❌ CI FAILED — Le code ne sera pas téléchargé.")
        print("   Corrige les erreurs et relance le script.")