"""
Script principal de génération des données Strava simulées.
- Au démarrage : génère l'historique des 12 derniers mois
- Toutes les heures : génère un batch de 5 à 10 nouvelles activités
Les fichiers JSON sont déposés dans OUTPUT_DIR pour être récupérés par Airbyte.
"""

import json
import os
import time
import logging
from datetime import datetime
from employees import load_employees
from activities import generate_history, generate_hourly_batch
from config import OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def save_to_json(records: list, prefix: str) -> str:
    """Sauvegarde les activités en JSON dans OUTPUT_DIR"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{OUTPUT_DIR}/{prefix}_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    logging.info(f"✅ {len(records)} activités sauvegardées → {filename}")
    return filename

def main():
    logging.info("🚀 Chargement des données RH...")
    df = load_employees()
    employees = df.to_dict(orient="records")
    logging.info(f"👥 {len(employees)} employés chargés")

    # ── Initialisation : historique 12 mois ──────────────────────
    logging.info("📅 Génération de l'historique 12 mois...")
    history = generate_history(employees)
    save_to_json(history, prefix="strava_history")
    logging.info(f"✅ Historique généré : {len(history)} activités")

    # ── Boucle horaire ───────────────────────────────────────────
    logging.info("⏰ Démarrage de la génération horaire...")
    while True:
        time.sleep(3600)  # Attente 1 heure
        logging.info("🔄 Génération du batch horaire...")
        batch = generate_hourly_batch(employees)
        save_to_json(batch, prefix="strava_batch")

if __name__ == "__main__":
    main()
