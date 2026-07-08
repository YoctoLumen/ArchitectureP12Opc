import os
import json
import glob
import logging
import psycopg2
from datetime import datetime
from employees import load_employees

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

OUTPUT_DIR  = os.getenv("OUTPUT_DIR",       "/tmp/json")
ARCHIVE_DIR = os.getenv("ARCHIVE_DIR",      "/tmp/json/archive")

DB = {
    "host":     os.getenv("POSTGRES_HOST",     "postgres"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB",       "poc_sport"),
    "user":     os.getenv("POSTGRES_USER",     "etl_user"),
    "password": os.getenv("POSTGRES_PASSWORD", "etl_password"),
}

def get_connection():
    try:
        conn = psycopg2.connect(**DB)
        log.info("✅ Connexion PostgreSQL établie")
        return conn
    except Exception as e:
        log.error(f"❌ Connexion PostgreSQL échouée : {e}")
        raise

def ingest_employees(conn):
    """Ingère les employés depuis Excel vers raw.employees."""
    log.info("👥 Chargement des employés depuis Excel...")
    df = load_employees()

    inserted = skipped = errors = 0

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            try:
                cur.execute("""
                    INSERT INTO raw.employees
                        (id, nom, prenom, adresse,
                         salaire_brut_annuel, mode_transport_declare, actif)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    row["id_salarie"],
                    row["nom"],
                    row["prenom"],
                    row["adresse"],
                    row.get("salaire_brut"),
                    row.get("mode_transport"),
                ))

                if cur.rowcount == 1:
                    inserted += 1
                else:
                    skipped += 1

            except Exception as e:
                errors += 1
                log.warning(f"  ⚠️ Erreur sur employé {row.get('id_salarie')} : {e}")
                conn.rollback()

    conn.commit()
    log.info(f"  ✅ {inserted} insérés | {skipped} doublons | {errors} erreurs")

def ingest_activities(conn):
    """Ingère les fichiers JSON Strava vers raw.activities."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    json_files = sorted(glob.glob(f"{OUTPUT_DIR}/strava_*.json"))
    if not json_files:
        log.warning("⚠️ Aucun fichier JSON Strava trouvé dans %s", OUTPUT_DIR)
        return

    for json_file in json_files:
        log.info(f"📄 Traitement : {json_file}")

        with open(json_file, "r", encoding="utf-8") as f:
            activities = json.load(f)

        inserted = skipped = errors = 0

        with conn.cursor() as cur:
            for act in activities:
                try:
                    cur.execute("""
                        INSERT INTO raw.activities
                            (id, id_salarie, date_debut, type,
                             distance_m, date_fin, commentaire, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        act["id"],
                        str(act["id_salarie"]),
                        act["date_debut"],
                        act["type"],
                        act.get("distance_m"),
                        act.get("date_fin"),
                        act.get("commentaire"),
                        act.get("source", "simulation"),
                    ))

                    if cur.rowcount == 1:
                        inserted += 1
                    else:
                        skipped += 1

                except Exception as e:
                    errors += 1
                    log.warning(f"  ⚠️ Erreur sur activité {act.get('id')} : {e}")
                    conn.rollback()

        conn.commit()
        log.info(f"  ✅ {inserted} insérées | {skipped} doublons | {errors} erreurs")

        # Archive le fichier traité
        archive_path = os.path.join(
            ARCHIVE_DIR,
            os.path.basename(json_file)
        )
        os.rename(json_file, archive_path)
        log.info(f"  📦 Archivé → {archive_path}")

def main():
    log.info("🚀 Démarrage ingestion JSON → PostgreSQL")
    conn = get_connection()
    try:
        ingest_employees(conn)
        ingest_activities(conn)
        log.info("✅ Ingestion terminée avec succès")
    except Exception as e:
        log.error(f"❌ Ingestion échouée : {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
