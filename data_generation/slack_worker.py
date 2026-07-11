import os
import json
import time
import logging
import boto3
from botocore.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
SQS_ENDPOINT   = os.getenv("SQS_ENDPOINT",      "http://localstack:4566")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME",    "alerts-declarations-queue")
AWS_REGION     = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL",  5))   
MAX_MESSAGES   = int(os.getenv("MAX_MESSAGES",   10))  


def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=SQS_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(retries={"max_attempts": 3}),
    )



def process_message(body: dict):
    """
    Simule l'envoi du message Slack.
    En production, remplacer ce bloc par un appel à l'API Slack réelle.
    """
    message = body.get("message", "")
    log.info("=" * 60)
    log.info("📣 [SLACK ÉMULÉ] #sport-entreprise")
    log.info(f"   {message}")
    log.info("=" * 60)


def poll_queue(sqs_client, queue_url: str):
    """Récupère et traite les messages de la queue SQS."""
    response = sqs_client.receive_message(
        QueueUrl            = queue_url,
        MaxNumberOfMessages = MAX_MESSAGES,
        WaitTimeSeconds     = 5,   
    )

    messages = response.get("Messages", [])
    if not messages:
        return

    log.info(f"📬 {len(messages)} message(s) reçu(s)")

    for msg in messages:
        try:
            body = json.loads(msg["Body"])
            process_message(body)

            sqs_client.delete_message(
                QueueUrl      = queue_url,
                ReceiptHandle = msg["ReceiptHandle"],
            )

        except json.JSONDecodeError as e:
            log.error(f"❌ Message JSON invalide : {e}")
        except Exception as e:
            log.error(f"❌ Erreur traitement message : {e}")


def get_queue_url(sqs_client) -> str:
    """Récupère ou crée la queue SQS."""
    try:
        response = sqs_client.get_queue_url(QueueName=SQS_QUEUE_NAME)
        return response["QueueUrl"]
    except sqs_client.exceptions.QueueDoesNotExist:
        log.warning(f"Queue '{SQS_QUEUE_NAME}' inexistante, création en cours...")
        response = sqs_client.create_queue(
            QueueName=SQS_QUEUE_NAME,
            Attributes={
                "VisibilityTimeout": "30",
                "MessageRetentionPeriod": "86400"
            }
        )
        log.info(f"Queue créée : {response['QueueUrl']}")
        return response["QueueUrl"]


def main():
    log.info("Démarrage du Slack Worker (émulation locale)")
    log.info(f"Queue : {SQS_QUEUE_NAME}")
    log.info(f"Endpoint : {SQS_ENDPOINT}")
    log.info(f"Polling : toutes les {POLL_INTERVAL}s")

    sqs_client = get_sqs_client()

    queue_url = get_queue_url(sqs_client)
    log.info(f"Connecté à la queue : {queue_url}")

    while True:
        try:
            poll_queue(sqs_client, queue_url)
        except Exception as e:
            log.error(f"Erreur polling : {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

