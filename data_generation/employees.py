import pandas as pd
import unicodedata
from config import RH_FILE_PATH, SPORT_FILE_PATH

def fix_encoding(value: str) -> str:
    """Corrige les problèmes d'encodage UTF-8 (ex: TimothÃ©e → Timothée)"""
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return value

def normalize_sport(sport: str) -> str:
    """Normalise les fautes de frappe dans les sports déclarés"""
    if not isinstance(sport, str):
        return None
    corrections = {"Runing": "Running", "runing": "Running"}
    return corrections.get(sport.strip(), sport.strip())

def load_employees() -> pd.DataFrame:
    """
    Charge et fusionne les fichiers RH et Sportif
    Retourne un DataFrame nettoyé
    """
    # Lecture des fichiers
    df_rh = pd.read_excel(RH_FILE_PATH, dtype={"ID salarié": str})
    df_sport = pd.read_excel(SPORT_FILE_PATH, dtype={"ID salarié": str})

    # Correction encodage sur toutes les colonnes texte
    for col in df_rh.select_dtypes(include="object").columns:
        df_rh[col] = df_rh[col].apply(fix_encoding)

    # Normalisation des sports
    df_sport["Pratique d'un sport"] = df_sport["Pratique d'un sport"].apply(normalize_sport)

    # Fusion sur l'ID salarié
    df = df_rh.merge(df_sport, on="ID salarié", how="left")

    # Renommage des colonnes pour simplifier
    df = df.rename(columns={
        "ID salarié":           "id_salarie",
        "Nom":                  "nom",
        "Prénom":               "prenom",
        "Adresse du domicile":  "adresse",
        "Moyen de déplacement": "mode_transport",
        "Salaire brut":         "salaire_brut",
        "Pratique d'un sport":  "sport_declare",
    })

    return df[["id_salarie", "nom", "prenom", "adresse", "mode_transport",
               "salaire_brut", "sport_declare"]]
