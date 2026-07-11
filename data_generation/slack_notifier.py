import os
import json
import logging
import boto3
from botocore.config import Config

log = logging.getLogger(__name__)

SQS_ENDPOINT = os.getenv("SQS_ENDPOINT", "http://localstack:4566")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "alerts-declarations-queue")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")

ACTIVITIES_WITH_DISTANCE = {
    "Course à pied",
    "Vélo",
    "Marche",
    "Running",
    "Trottinette",
    "Natation",
}

TEMPLATES = {
    "Course à pied": {
        "message": (
            "🏃 Bravo {prenom} {nom} ! "
            "Tu viens de courir {distance_km} km en {duree_min} min ! "
            "Quelle énergie ! 🔥🏅"
        ),
        "avec_distance": True,
    },
    "Randonnée": {
        "message": (
            "🌄 Magnifique {prenom} {nom} ! "
            "Une randonnée de {distance_km} km terminée"
            "{commentaire_part} 🏕️"
        ),
        "avec_distance": True,
    },
    "Vélo": {
        "message": (
            "🚴 Super {prenom} {nom} ! "
            "{distance_km} km à vélo aujourd'hui ! "
            "La planète te remercie 🌿"
        ),
        "avec_distance": True,
    },
    "Marche": {
        "message": (
            "🚶 Bravo {prenom} {nom} ! "
            "{distance_km} km à pied, c'est excellent pour la santé ! 💪"
        ),
        "avec_distance": True,
    },
    "default": {
        "message": (
            "⭐ Félicitations {prenom} {nom} ! "
            "Tu viens de terminer une session de {type} ! "
            "Continue comme ça ! 💪"
        ),
        "avec_distance": False,
    },
}


def _get_sqs_client():
    """Retourne un client SQS pointant vers LocalStack."""
    return boto3.client(
        "sqs",
        endpoint_url=SQS_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(retries={"max_attempts": 3}),
    )


def _get_queue_url(sqs_client) -> str:
    """Récupère l'URL de la queue SQS."""
    response = sqs_client.get_queue_url(QueueName=SQS_QUEUE_NAME)
    return response["QueueUrl"]


def _format_message(activity: dict, employee: dict) -> str:
    """
    Formate le message Slack selon le type d'activité.
    Respecte les templates de la note de cadrage.
    """
    prenom   = employee.get("prenom", "")
    nom      = employee.get("nom", "")
    type_act = activity.get("type", "")
    duree_s  = activity.get("duree_s", 0) or 0
    duree_min = round(duree_s / 60) if duree_s else None
    distance_m  = activity.get("distance_m")
    distance_km = round(distance_m / 1000, 1) if distance_m else None
    commentaire = activity.get("commentaire", "")
    commentaire_part = (
        f' et un nouveau spot à découvrir ! ("{commentaire}")'
        if commentaire
        else " et un nouveau spot à découvrir !"
    )

    template = TEMPLATES.get(type_act, TEMPLATES["default"])

    try:
        message = template["message"].format(
            prenom=prenom,
            nom=nom,
            type=type_act,
            distance_km=distance_km if distance_km else "N/A",
            duree_min=duree_min if duree_min else "N/A",
            commentaire_part=commentaire_part,
        )
    except KeyError as e:
        log.warning(f"Clé manquante dans le template '{type_act}' : {e}")
        message = TEMPLATES["default"]["message"].format(
            prenom=prenom,
            nom=nom,
            type=type_act,
        )

    return message


def send_slack_alert(activity: dict, employee: dict) -> bool:
    try:
        message = _format_message(activity, employee)

        payload = {
            "message": message,
            "activity_id": str(activity.get("id", "")),
            "id_salarie": str(activity.get("id_salarie", "")),
            "type": activity.get("type", ""),
            "sent_at": activity.get("date_debut", ""),
        }

        sqs_client = _get_sqs_client()
        queue_url = _get_queue_url(sqs_client)

        sqs_client.send_message(
            QueueUrl = queue_url,
            MessageBody = json.dumps(payload, ensure_ascii=False),
        )

        log.info(f"Alerte SQS envoyée pour {employee.get('prenom')} "
                 f"{employee.get('nom')} — {activity.get('type')}")
        return True

    except Exception as e:
        log.error(f"Échec envoi alerte SQS : {e}")
        return False
