
RH_FILE_PATH = "/tmp/excel/DonneesRH.xlsx"
SPORT_FILE_PATH = "/tmp/excel/DonneesSportive.xlsx"

OUTPUT_DIR = "/tmp/json"

HISTORY_MONTHS = 12
MIN_ACTIVITIES_INIT = 10   
MAX_ACTIVITIES_INIT = 80   

MIN_ACTIVITIES_HOURLY = 5
MAX_ACTIVITIES_HOURLY = 10

ELIGIBILITY_THRESHOLD = 15

PROBA_ACTIVITY_NO_SPORT = 0.4

SPORT_TO_STRAVA = {
    "Running":        [("Run", 8), ("Walk", 2)],
    "Randonnée":      [("Hike", 8), ("Walk", 2)],
    "Natation":       [("Swim", 9), ("Workout", 1)],
    "Triathlon":      [("Run", 4), ("Swim", 3), ("Ride", 3)],
    "Tennis":         [("Workout", 10)],
    "Badminton":      [("Workout", 10)],
    "Tennis de table":[("Workout", 10)],
    "Football":       [("Workout", 8), ("Run", 2)],
    "Rugby":          [("Workout", 8), ("Run", 2)],
    "Basketball":     [("Workout", 8), ("Run", 2)],
    "Judo":           [("Workout", 10)],
    "Boxe":           [("Workout", 10)],
    "Escalade":       [("Workout", 10)],
    "Voile":          [("Workout", 10)],
    "Équitation":     [("Workout", 10)],
    "default":        [("Walk", 5), ("Run", 3), ("Ride", 2)],
}

DISTANCE_RANGES = {
    "Run":     (2_000,  25_000),
    "Ride":    (5_000,  80_000),
    "Walk":    (1_000,  15_000),
    "Hike":    (3_000,  30_000),
    "Swim":    (500,     5_000),
    "Workout": (None,     None),   # Non pertinent
}

DURATION_RANGES = {
    "Run":     (20,  120),
    "Ride":    (30,  240),
    "Walk":    (15,  180),
    "Hike":    (60,  480),
    "Swim":    (20,   90),
    "Workout": (30,   90),
}

COMMENTS = {
    "Run": [
        "Super sortie matinale ! 🏃",
        "Jambes lourdes mais on lâche rien 💪",
        "Nouveau record personnel ! 🏅",
        "Belle foulée ce soir !",
        None,
    ],
    "Hike": [
        "Randonnée de St Guilhem le désert, je vous la conseille c'est top 🌿",
        "Vue magnifique au sommet ! 🏔️",
        "Parfait pour se ressourcer",
        "Sentier du Pic Saint-Loup, incroyable ! ⛰️",
        None,
    ],
    "Ride": [
        "Belle sortie vélo ce matin ! 🚴",
        "Les cols c'est la vie !",
        "Petite sortie tranquille 🌅",
        None,
    ],
    "Walk": [
        "Belle balade digestive 🚶",
        "Marche matinale pour bien commencer la journée",
        None,
    ],
    "Swim": [
        "Bonne session piscine 🏊",
        "Crawl et brasse au programme !",
        "Séance intensive aujourd'hui 💦",
        None,
    ],
    "Workout": [
        "Séance muscu intense 💪",
        "Bon entraînement !",
        "On donne tout ! 🔥",
        None,
    ],
}
