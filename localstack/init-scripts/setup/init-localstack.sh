#!/bin/bash

echo "🚀 Démarrage de l'initialisation LocalStack..."

REGION="eu-west-1"

echo "📨 Création de la queue SQS pour les alertes Slack..."

awslocal sqs create-queue \
  --queue-name alerts-declarations-queue \
  --region $REGION \
  --attributes '{
    "VisibilityTimeout": "30",
    "MessageRetentionPeriod": "86400"
  }'
echo "  ✅ Queue alerts-declarations-queue créée"

echo ""
echo "📋 Vérification de l'initialisation..."
echo "  Queues SQS :"
awslocal sqs list-queues --region $REGION

echo ""
echo "✅ Initialisation LocalStack terminée avec succès !"
