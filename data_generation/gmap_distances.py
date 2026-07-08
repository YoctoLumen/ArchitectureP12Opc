import os
import logging
import psycopg2
import requests
import time
import unicodedata
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

ORS_API_KEY   = os.getenv("ORS_API_KEY")
ORS_URL       = "https://api.openrouteservice.org/v2/directions/{profile}"
BUREAU_COORDS = (3.8993, 43.5698)  # lon, lat — 1362 Av. des Platanes, 34970 Lattes

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST"),
    "port":     int(os.getenv("POSTGRES_PORT")),
    "dbname":   os.getenv("POSTGRES_DB"),
    "user":     os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}

# Profils ORS : https://openrouteservice.org/dev/#/api-docs
ORS_PROFILE = {
    "driving":   "driving-car",
    "walking":   "foot-walking",
    "bicycling": "cycling-regular",
}

REGLES_RAW = [
    {"mots_cles": ["vehicule", "thermique", "electrique"], "max_m": 50_000, "mode": "driving"},
    {"mots_cles": ["transport", "commun"],                 "max_m": 50_000, "mode": "driving"},
    {"mots_cles": ["marche", "running"],                   "max_m": 15_000, "mode": "walking"},
    {"mots_cles": ["velo", "trottinette", "autres"],       "max_m": 25_000, "mode": "bicycling"},
]

def strip_accents(s):
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("utf-8").lower().strip()

def get_regle(mode):
    mode_normalise = strip_accents(mode)
    for regle in REGLES_RAW:
        if any(mot in mode_normalise for mot in regle["mots_cles"]):
            return regle
    return None

def geocode(adresse):
    """Adresse → coordonnées GPS via ORS Geocoding (Pelias)."""
    try:
        r = requests.get(
            "https://api.openrouteservice.org/geocode/search",
            params={
                "api_key": ORS_API_KEY,
                "text":    adresse,
                "size":    1
            },
            timeout=10
        )
        data = r.json()
        coords = data["features"][0]["geometry"]["coordinates"]
        return coords[0], coords[1]  # lon, lat
    except Exception as e:
        log.error(f"❌ Geocode error pour '{adresse}' : {e}")
        return None

def get_distance(adresse, mode):
    """Coordonnées GPS → distance en mètres via ORS Directions."""
    try:
        coords_origine = geocode(adresse)
        if not coords_origine:
            return None

        profile = ORS_PROFILE.get(mode, "driving-car")
        lon1, lat1 = coords_origine
        lon2, lat2 = BUREAU_COORDS

        r = requests.post(
            ORS_URL.format(profile=profile),
            headers={
                "Authorization": ORS_API_KEY,
                "Content-Type":  "application/json"
            },
            json={
                "coordinates": [[lon1, lat1], [lon2, lat2]]
            },
            timeout=10
        )
        data = r.json()
        return int(data["routes"][0]["summary"]["distance"])
    except Exception as e:
        log.error(f"❌ ORS Directions error : {e}")
        return None

def valider(distance_m, mode_declare):
    regle = get_regle(mode_declare)
    if not regle:
        return False, f"Mode non reconnu : '{mode_declare}'"
    if distance_m is None:
        return False, "Distance non calculable"
    if distance_m > regle["max_m"]:
        return False, (f"{distance_m/1000:.1f} km > seuil "
                       f"{regle['max_m']/1000:.0f} km pour '{mode_declare}'")
    return True, None

def main():
    log.info("🚀 Calcul distances — OpenRouteService")
    conn = psycopg2.connect(**DB_CONFIG)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, nom, prenom, adresse, code_postal, ville, mode_transport_declare
            FROM raw.employees
            WHERE actif = TRUE
              AND id NOT IN (SELECT DISTINCT id_salarie FROM raw.distances)
        """)
        cols      = [d[0] for d in cur.description]
        employees = [dict(zip(cols, row)) for row in cur.fetchall()]

    log.info(f"👥 {len(employees)} salariés à traiter")
    ok = ko = 0

    for emp in employees:
        mode    = emp["mode_transport_declare"] or ""
        adresse = ", ".join(filter(None, [
            emp["adresse"], emp["code_postal"], emp["ville"], "France"
        ]))

        regle      = get_regle(mode)
        distance_m = get_distance(adresse, regle["mode"]) if regle else None
        valide, motif = valider(distance_m, mode)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO raw.distances
                    (id_salarie, distance_m, mode_transport, valide, motif_rejet, calcule_le)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (emp["id"], distance_m or 0, mode, valide, motif, datetime.now()))
        conn.commit()

        status = "✅" if valide else "❌"
        log.info(f"  {status} {emp['prenom']} {emp['nom']} — "
                 f"{(distance_m or 0)/1000:.1f} km ({mode}) {motif or ''}")

        ok += valide
        ko += not valide
        time.sleep(1.5)  # ⚠️ ORS free tier : 40 req/min

    conn.close()
    log.info(f"✅ Terminé — {ok} valides, {ko} rejets")

if __name__ == "__main__":
    main()
