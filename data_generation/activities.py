import uuid
import random
from datetime import datetime, timedelta
from config import (
    SPORT_TO_STRAVA, DISTANCE_RANGES, DURATION_RANGES, COMMENTS,
    PROBA_ACTIVITY_NO_SPORT
)

def pick_activity_type(sport: str) -> str:
    """Choisit un type d'activité Strava selon le sport déclaré"""
    mapping = SPORT_TO_STRAVA.get(sport, SPORT_TO_STRAVA["default"])
    types, weights = zip(*mapping)
    return random.choices(types, weights=weights, k=1)[0]

def generate_activity(employee: dict, activity_date: datetime) -> dict:
    """Génère une activité Strava simulée pour un employé"""
    sport = employee.get("sport_declare")
    activity_type = pick_activity_type(sport)

    dist_range = DISTANCE_RANGES[activity_type]
    distance = (
        random.randint(*dist_range) if dist_range[0] else None
    )

    dur_range = DURATION_RANGES[activity_type]
    duration = random.randint(*dur_range)
    date_fin = activity_date + timedelta(minutes=duration)

    comment = random.choice(COMMENTS.get(activity_type, [None]))

    return {
        "id":           str(uuid.uuid4()),
        "id_salarie":   str(employee["id_salarie"]),
        "date_debut":   activity_date.isoformat(),
        "type":         activity_type,
        "distance_m":   distance,
        "date_fin":     date_fin.isoformat(),
        "commentaire":  comment,
        "source":       "simulation",
    }

def should_generate(sport: str) -> bool:
    """Détermine si un employé sans sport déclaré peut avoir des activités"""
    if sport:
        return True
    return random.random() < PROBA_ACTIVITY_NO_SPORT

def generate_history(employees: list) -> list:
    """Génère l'historique des 12 derniers mois pour tous les employés"""
    from config import (
        HISTORY_MONTHS, MIN_ACTIVITIES_INIT, MAX_ACTIVITIES_INIT,
        ELIGIBILITY_THRESHOLD
    )
    records = []
    start_date = datetime.now() - timedelta(days=365)

    for emp in employees:
        if not should_generate(emp["sport_declare"]):
            continue

        if emp["sport_declare"]:
            nb = random.randint(
                ELIGIBILITY_THRESHOLD - 5,
                MAX_ACTIVITIES_INIT
            )
        else:
            nb = random.randint(MIN_ACTIVITIES_INIT // 2, MIN_ACTIVITIES_INIT)

        for _ in range(nb):
            random_offset = random.randint(0, 365)
            activity_date = start_date + timedelta(
                days=random_offset,
                hours=random.randint(6, 21),
                minutes=random.randint(0, 59)
            )
            records.append(generate_activity(emp, activity_date))

    return records

def generate_hourly_batch(employees: list) -> list:
    """Génère 5 à 10 nouvelles activités pour la simulation continue"""
    from config import MIN_ACTIVITIES_HOURLY, MAX_ACTIVITIES_HOURLY
    nb = random.randint(MIN_ACTIVITIES_HOURLY, MAX_ACTIVITIES_HOURLY)
    selected = random.choices(employees, k=nb)
    now = datetime.now()

    return [
        generate_activity(
            emp,
            now - timedelta(minutes=random.randint(0, 59))
        )
        for emp in selected
    ]
