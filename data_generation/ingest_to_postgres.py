import os
import json
import glob
import logging
import psycopg2
import re
from datetime import datetime
from slack_notifier import send_slack_alert
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

def parse_adresse(adresse: str):
    if not isinstance(adresse, str) or ',' not in adresse:
        log.warning(f"Format d'adresse non reconnu : {adresse}")
        return adresse, None, None

    try:
        parties = adresse.split(',', 1)
        rue = parties[0].strip()
        cp_ville = parties[1].strip()

        match = re.match(r'^(\d{5})\s+(.+)$', cp_ville)
        if match:
            code_postal = match.group(1)
            ville = match.group(2).strip()
        else:
            log.warning(f"Code postal non trouvé dans : {cp_ville}")
            code_postal = None
            ville = cp_ville

        return rue, code_postal, ville

    except Exception as e:
        log.warning(f"Erreur adresse '{adresse}' : {e}")
        return adresse, None, None
    
def ingest_employees(conn):
    log.info("👥 Chargement des employés depuis Excel...")
    df = load_employees()

    inserted = skipped = errors = 0

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            try:
                rue, code_postal, ville = parse_adresse(row.get("adresse"))
                cur.execute("""
                    INSERT INTO raw.employees
                        (id, nom, prenom, code_postal, ville, adresse,
                         salaire_brut_annuel, date_embauche, mode_transport_declare, actif)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (id) DO UPDATE SET
                        adresse                 = EXCLUDED.adresse,
                        code_postal             = EXCLUDED.code_postal,
                        ville                   = EXCLUDED.ville,
                        salaire_brut_annuel     = EXCLUDED.salaire_brut_annuel,
                        mode_transport_declare  = EXCLUDED.mode_transport_declare,
                        date_embauche           = EXCLUDED.date_embauche,
                        inserted_at             = now()
                """, (
                    row["id_salarie"],
                    row["nom"],
                    row["prenom"],
                    code_postal,
                    ville,
                    row["adresse"],
                    row.get("salaire_brut"),
                    row.get("date_embauche"),
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
                        cur.execute("""
                            SELECT prenom, nom
                            FROM raw.employees
                            WHERE id = %s
                        """, (str(act["id_salarie"]),))
                        emp_row = cur.fetchone()

                        if emp_row:
                            employee = {
                                "prenom": emp_row[0],
                                "nom":    emp_row[1],
                            }
                            send_slack_alert(act, employee)
                    else:
                        skipped += 1

                except Exception as e:
                    errors += 1
                    log.warning(f"  ⚠️ Erreur sur activité {act.get('id')} : {e}")
                    conn.rollback()

        conn.commit()
        log.info(f"  ✅ {inserted} insérées | {skipped} doublons | {errors} erreurs")

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
