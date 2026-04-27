"""
🎌 AniData Lab — Nettoyage du dataset anime.csv
=================================================
Ce script :
- charge le fichier data/anime.csv
- nettoie les colonnes
- traite les NaN déguisés
- supprime les doublons
- corrige les types
- normalise certaines colonnes texte
- extrait les dates de début/fin depuis 'aired'
- marque certains outliers
- exporte le fichier nettoyé dans output/anime_cleaned.csv
"""

import os
import sys
import pandas as pd
import numpy as np

# ============================================
# CONFIG
# ============================================
DATA_DIR = "data"
OUTPUT_DIR = "output"
INPUT_FILE = os.path.join(DATA_DIR, "anime.csv")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "anime_cleaned.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================
# AFFICHAGE CONSOLE
# ============================================
class C:
    H = "\033[95m"
    B = "\033[94m"
    G = "\033[92m"
    W = "\033[93m"
    F = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"


def titre(t):
    print(f"\n{C.BOLD}{C.H}{'='*60}\n  {t}\n{'='*60}{C.END}\n")


def step(t):
    print(f"\n{C.BOLD}{C.B}--- {t} ---{C.END}")


def ok(t):
    print(f"  {C.G}✅ {t}{C.END}")


def warn(t):
    print(f"  {C.W}⚠️  {t}{C.END}")


def info(t):
    print(f"  {C.B}ℹ️  {t}{C.END}")


def delta(before, after, label):
    diff = before - after
    pct = (diff / before * 100) if before else 0
    print(f"  {C.G}✅ {label} : {before:,} → {after:,} ({diff:,} retirées, -{pct:.1f}%){C.END}")


# ============================================
# CHARGEMENT
# ============================================
titre("NETTOYAGE — anime.csv")

if not os.path.exists(INPUT_FILE):
    print(f"{C.F}❌ Fichier introuvable : {INPUT_FILE}{C.END}")
    sys.exit(1)

print("  Chargement du fichier brut...")

# Ton CSV utilise ; et contient une première ligne parasite
df_raw = pd.read_csv(INPUT_FILE, sep=";", skiprows=1)

ok(f"Fichier chargé : {df_raw.shape[0]:,} lignes × {df_raw.shape[1]} colonnes")

# Copie de travail
df = df_raw.copy()
n_initial = len(df)

print(f"\n  Colonnes : {list(df.columns)}")


# ============================================
# ÉTAPE 1 — NORMALISATION DES NOMS DE COLONNES
# ============================================
step("Étape 1 : Normalisation des noms de colonnes")

old_cols = list(df.columns)

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace("-", "_", regex=False)
)

new_cols = list(df.columns)
renamed = [(o, n) for o, n in zip(old_cols, new_cols) if o != n]

if renamed:
    for old, new in renamed:
        info(f"'{old}' → '{new}'")
    ok(f"{len(renamed)} colonne(s) renommée(s)")
else:
    ok("Noms de colonnes déjà normalisés")


# ============================================
# ÉTAPE 2 — SUPPRESSION DES DOUBLONS
# ============================================
step("Étape 2 : Suppression des doublons")

n_before = len(df)

# Doublons exacts
doublons_exact = df.duplicated().sum()
if doublons_exact > 0:
    df = df.drop_duplicates()
    warn(f"{doublons_exact:,} doublons exacts supprimés")
else:
    ok("Aucun doublon exact")

# Doublons sur identifiant
id_col = None
for candidate in ["mal_id", "anime_id", "uid", "id"]:
    if candidate in df.columns:
        id_col = candidate
        break

if id_col:
    doublons_id = df[id_col].duplicated().sum()
    if doublons_id > 0:
        df = df.drop_duplicates(subset=[id_col], keep="first")
        warn(f"{doublons_id:,} doublons sur '{id_col}' supprimés")
    else:
        ok(f"Clé '{id_col}' : aucun doublon")

delta(n_before, len(df), "Doublons")


# ============================================
# ÉTAPE 3 — TRAITEMENT DES NaN DÉGUISÉS
# ============================================
step("Étape 3 : Traitement des NaN déguisés")

nan_values = [
    "Unknown", "unknown", "UNKNOWN",
    "N/A", "n/a", "NA",
    "None", "none",
    "-", ".", "", " "
]

replacements = 0

for col in df.select_dtypes(include=["object"]).columns:
    mask = df[col].isin(nan_values)
    count = mask.sum()
    if count > 0:
        df.loc[mask, col] = np.nan
        replacements += count
        info(f"'{col}' : {count:,} valeurs suspectes → NaN")

ok(f"Total : {replacements:,} valeurs textuelles remplacées par NaN")

# score = 0 considéré comme absence de score
score_col = "score" if "score" in df.columns else None
if score_col:
    df[score_col] = pd.to_numeric(df[score_col], errors="coerce")
    score_zeros = (df[score_col] == 0).sum()
    if score_zeros > 0:
        df.loc[df[score_col] == 0, score_col] = np.nan
        warn(f"'{score_col}' : {score_zeros:,} scores à 0 → NaN")


# ============================================
# ÉTAPE 4 — CORRECTION DES TYPES
# ============================================
step("Étape 4 : Correction des types de données")

numeric_candidates = [
    "mal_id", "episodes", "ranked", "popularity", "members",
    "favorites", "score", "watching", "completed", "on_hold",
    "dropped", "plan_to_watch", "score_10", "score_9", "score_8",
    "score_7", "score_6", "score_5", "score_4", "score_3",
    "score_2", "score_1"
]

conversions = 0

for col in numeric_candidates:
    if col in df.columns:
        before_nan = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_nan = df[col].isna().sum()
        new_nan = after_nan - before_nan

        if new_nan > 0:
            info(f"'{col}' : conversion numérique, {new_nan:,} valeur(s) → NaN")
        else:
            info(f"'{col}' : conversion numérique ok")

        conversions += 1

# Colonnes entières nullable
int_candidates = [
    "mal_id", "episodes", "ranked", "popularity", "members",
    "favorites", "watching", "completed", "on_hold",
    "dropped", "plan_to_watch", "score_10", "score_9", "score_8",
    "score_7", "score_6", "score_5", "score_4", "score_3",
    "score_2", "score_1"
]

for col in int_candidates:
    if col in df.columns:
        try:
            df[col] = df[col].astype("Int64")
        except Exception:
            pass

ok(f"{conversions} colonne(s) converties")

print("\n  Types après correction :")
for col in df.columns:
    print(f"    • {col:25s} → {str(df[col].dtype):15s}")


# ============================================
# ÉTAPE 5 — NETTOYAGE DES COLONNES TEXTUELLES
# ============================================
step("Étape 5 : Nettoyage des colonnes textuelles")

text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

for col in text_cols:
    df[col] = df[col].astype("string")
    df[col] = df[col].str.strip()
    df[col] = df[col].str.replace(r"\s+", " ", regex=True)

ok(f"{len(text_cols)} colonnes textuelles nettoyées")

# Nettoyage léger des colonnes de noms
name_cols = [c for c in df.columns if "name" in c]
for col in name_cols:
    df[col] = df[col].str.replace('"', "", regex=False)
    info(f"'{col}' : guillemets parasites supprimés")


# ============================================
# ÉTAPE 6 — COLONNES MULTI-VALUÉES
# ============================================
step("Étape 6 : Normalisation des colonnes multi-valuées")

multi_value_cols = [c for c in ["genres", "producers", "licensors", "studios"] if c in df.columns]

def clean_list(val):
    if pd.isna(val):
        return np.nan
    items = [item.strip() for item in str(val).split(",")]
    items = [item for item in items if item not in ["", "Unknown", "unknown"]]
    return ", ".join(items) if items else np.nan

for col in multi_value_cols:
    has_comma = df[col].dropna().astype(str).str.contains(",").any()
    if has_comma:
        df[col] = df[col].apply(clean_list)
        n_unique = df[col].dropna().str.split(", ").explode().nunique()
        ok(f"'{col}' nettoyée — {n_unique:,} valeur(s) uniques")
    else:
        info(f"'{col}' : pas de liste à normaliser")


# ============================================
# ÉTAPE 7 — DATES
# ============================================
step("Étape 7 : Normalisation des dates")

if "aired" in df.columns:
    aired_split = df["aired"].astype("string").str.split(" to ", n=1, expand=True)

    if aired_split.shape[1] >= 1:
        df["aired_start"] = pd.to_datetime(aired_split[0], errors="coerce")
    if aired_split.shape[1] >= 2:
        df["aired_end"] = pd.to_datetime(aired_split[1], errors="coerce")

    ok("'aired' → 'aired_start' et 'aired_end'")

if "premiered" in df.columns:
    # On garde premiered en texte, souvent sous forme "Spring 2006"
    df["premiered"] = df["premiered"].astype("string").str.strip()
    ok("'premiered' nettoyée en texte")


# ============================================
# ÉTAPE 8 — OUTLIERS
# ============================================
step("Étape 8 : Détection et marquage des outliers")

df["is_outlier"] = False

if "score" in df.columns:
    mask_score = df["score"].notna() & ((df["score"] < 1) | (df["score"] > 10))
    if mask_score.sum() > 0:
        df.loc[mask_score, "is_outlier"] = True
        warn(f"Score hors bornes : {mask_score.sum():,}")

if "episodes" in df.columns:
    mask_ep = df["episodes"].notna() & (df["episodes"] > 5000)
    if mask_ep.sum() > 0:
        df.loc[mask_ep, "is_outlier"] = True
        warn(f"Episodes > 5000 : {mask_ep.sum():,}")

if "members" in df.columns:
    mask_mem = df["members"].notna() & (df["members"] == 0)
    if mask_mem.sum() > 0:
        df.loc[mask_mem, "is_outlier"] = True
        warn(f"Members = 0 : {mask_mem.sum():,}")

total_outliers = int(df["is_outlier"].sum())
ok(f"Total outliers marqués : {total_outliers:,}")


# ============================================
# RAPPORT FINAL
# ============================================
titre("RAPPORT DE NETTOYAGE")

n_final = len(df)
nan_before = int(df_raw.isnull().sum().sum())
nan_after = int(df.isnull().sum().sum())

print(f"""
{C.BOLD}                          AVANT           APRÈS{C.END}
{"─"*55}
  Lignes                  {n_initial:>10,}      {n_final:>10,}
  Colonnes                {df_raw.shape[1]:>10}      {df.shape[1]:>10}
  NaN classiques          {nan_before:>10,}      {nan_after:>10,}
  Outliers marqués                        {total_outliers:>10,}
""")

print("  Valeurs manquantes restantes par colonne :")
missing = df.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)

if len(missing) > 0:
    for col, count in missing.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"    {col:25s} {count:>7,}  ({pct:5.1f}%) {bar}")
else:
    ok("Aucune valeur manquante")


# ============================================
# EXPORT
# ============================================
step("Export du fichier nettoyé")

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8", sep=";")

taille = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
ok(f"Fichier exporté : {OUTPUT_FILE} ({taille:.1f} MB)")
ok(f"{df.shape[0]:,} lignes × {df.shape[1]} colonnes")

print(f"\n{C.BOLD}{C.G}✅ Nettoyage terminé !{C.END}\n")