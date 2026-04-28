#!/usr/bin/env python3
"""
sync.py — Vérifie le dernier run GitHub Actions sur la branche ethan.
Si tous les tests passent → git pull --rebase automatiquement.

Usage :
    python sync.py
    python sync.py --wait   # attend que le run en cours se termine
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime

import urllib.request
import urllib.error
import json

REPO    = "AnjaraAndriatseheno/Projet_AniData"
BRANCH  = "ethan"
API_URL = f"https://api.github.com/repos/{REPO}/actions/runs?branch={BRANCH}&per_page=1"


def fetch_latest_run() -> dict:
    req = urllib.request.Request(
        API_URL,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "sync-script"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    runs = data.get("workflow_runs", [])
    if not runs:
        print("Aucun run trouvé sur la branche ethan.")
        sys.exit(1)
    return runs[0]


def print_run_info(run: dict) -> None:
    print(f"  Run      : {run['name']} #{run['run_number']}")
    print(f"  Statut   : {run['status']}")
    print(f"  Résultat : {run.get('conclusion') or '(en cours)'}")
    print(f"  Déclenché: {run['head_commit']['message']!r}")
    print(f"  Lien     : {run['html_url']}")


def git_pull() -> bool:
    print("\nRécupération du code...")
    result = subprocess.run(
        ["git", "pull", "--rebase", "origin", BRANCH],
        capture_output=True, text=True
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
    return result.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync local si GitHub Actions OK.")
    parser.add_argument("--wait", action="store_true",
                        help="Attendre que le run en cours se termine avant de vérifier.")
    args = parser.parse_args()

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Vérification GitHub Actions — branche {BRANCH}")

    run = fetch_latest_run()

    if args.wait:
        while run["status"] not in ("completed",):
            print(f"  Run en cours ({run['status']})... attente 15s")
            time.sleep(15)
            run = fetch_latest_run()

    print_run_info(run)

    if run["status"] != "completed":
        print("\nLe run n'est pas encore terminé. Relance avec --wait pour patienter.")
        sys.exit(0)

    conclusion = run.get("conclusion")

    if conclusion == "success":
        print("\n✓ Tous les tests sont passés.")
        if git_pull():
            print("✓ Code mis à jour localement.")
        else:
            print("✗ Erreur lors du git pull.")
            sys.exit(1)
    else:
        print(f"\n✗ Run échoué ({conclusion}) — voir : {run['html_url']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
