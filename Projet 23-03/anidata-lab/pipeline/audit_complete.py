"""
🎌 AniData Lab — Script d'audit du dataset MyAnimeList
=======================================================
Séance 1 — Lundi 23 mars 2026 — Après-midi

Ce script réalise un audit complet des 3 fichiers CSV :
  - anime.csv (17 562 animes)
  - rating_complete.csv (57M ratings)
  - anime_with_synopsis.csv (~17 000 synopsis)

Usage : python 01_audit_complet.py
Prérequis : pip install pandas matplotlib seaborn
"""

import pandas as pd
import os
import sys

# ============================================
# CONFIGURATION
# ============================================
DATA_DIR = "data"  # Chemin vers le dossier data/

# Couleurs terminal
class C:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def titre(text):
    """Affiche un titre de section."""
    print(f"\n{C.BOLD}{C.HEADER}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{C.END}\n")


def sous_titre(text):
    """Affiche un sous-titre."""
    print(f"\n{C.BOLD}{C.CYAN}--- {text} ---{C.END}")


def ok(text):
    print(f"  {C.GREEN}✅ {text}{C.END}")


def warn(text):
    print(f"  {C.WARNING}⚠️  {text}{C.END}")


def fail(text):
    print(f"  {C.FAIL}❌ {text}{C.END}")


def info(text):
    print(f"  {C.BLUE}ℹ️  {text}{C.END}")


# ============================================
# VÉRIFICATION DES FICHIERS
# ============================================
titre("1. VÉRIFICATION DES FICHIERS")

fichiers = {
    "anime.csv": "Informations générales sur les animes",
    "rating_complete.csv": "Ratings des utilisateurs (animes complétés)",
    "anime_with_synopsis.csv": "Synopsis textuels des animes",
}

fichiers_ok = True
for fichier, description in fichiers.items():
    chemin = os.path.join(DATA_DIR, fichier)
    if os.path.exists(chemin):
        taille = os.path.getsize(chemin) / (1024 * 1024)
        ok(f"{fichier} ({taille:.1f} MB) — {description}")
    else:
        fail(f"{fichier} — MANQUANT !")
        fichiers_ok = False

if not fichiers_ok:
    print(f"\n{C.FAIL}Des fichiers sont manquants !")
    print(f"Téléchargez-les depuis : https://www.kaggle.com/datasets/hernan4444/anime-recommendation-database-2020{C.END}")
    sys.exit(1)


# ============================================
# CHARGEMENT DES DONNÉES
# ============================================
titre("2. CHARGEMENT DES DONNÉES")

print("  Chargement de anime.csv...")
anime = pd.read_csv(os.path.join(DATA_DIR, "anime.csv"))
ok(f"anime.csv : {anime.shape[0]:,} lignes × {anime.shape[1]} colonnes")

print("  Chargement de anime_with_synopsis.csv...")
