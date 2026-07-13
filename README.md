

# Gérez un projet d'infrastructure - Projet 12 Data Engineer

Projet de création d'une infrastructure de données, automatisation d'un pipeline etl et creation d'un dashboard. L'ensemble du projet est réalisé dans le cadre de la formation Openclassroom Data Engineer.



## Table des matières
1. [Contexte et objectifs](#contexte)
2. [Architecture du projet](#architecture)
3. [Prérequis](#prérequis)
4. [Installation et lancement](#installation)
5. [Structure du projet](#structure)
6. [Description des composants](#composants)
7. [Variables d'environnement](#variables)


## Contexte et objectifs

Il s'agit d'un poc réalisé dans le cadre d'une mission fictive ayant comme objectifs la mise en place complête d'une architecture ainsi que la communication de résultat/kpi propre à l'entreprise. On souhaite connaitre l'impact d'un changement de politique de l'entreprise vis à vis de ses salariés et conditions de vie. 

## Architecture du projet

Le projet est réalisé via Docker afin de simulé une architecture Cloud

<img width="806" height="781" alt="Capture d’écran 2026-07-13 093908" src="https://github.com/user-attachments/assets/9b2b7e7c-65fe-4aa9-8b21-98b80a2cd490" />


## Prérequis

- [Docker](https://www.docker.com/) >= 24.x
- [Docker Compose](https://docs.docker.com/compose/) >= 2.x
- [Power BI Desktop](https://powerbi.microsoft.com/) (pour la visualisation)
- Une clé API **OpenRouteService** (pour le calcul des distances domicile/travail)
- Une version community de [Localstack](https://www.localstack.cloud/)
- L'accès à Kestra, Postgres et Python
- L'accès aux librairies Python présente dans le fichier requirements.txt

## Installation et lancement

### 1. Cloner le dépôt
bash
git clone https://github.com/YoctoLumen/ArchitectureP12Opc.git
cd poc-avantages-sportifs


### 2. Configurer les variables d'environnement
bash
cp .env.example .env
# Éditez le fichier .env avec vos propres valeurs


### 3. Lancer l'ensemble des conteneurs
bash
docker-compose up -d

### 4. Vérifier que les conteneurs sont actifs
bash
docker-compose ps

### 5. Accéder aux interfaces
| Service | URL | Identifiants par défaut |
|---|---|---|
| Kestra UI | http://localhost:8080 | admin / admin |
| PostgreSQL | localhost:5432 | Voir `.env` |

## Structure du projet

- 📄 `compose.yml` — Orchestration des conteneurs
- 🔐 `.env` — Variables d'environnement

- 📂 **kestra/** — Workflows Kestra
  - 📂 **flows/**
    - 📄 `poc_sport_pipeline.yml` — Pipeline complet

- 📂 **dbt/** — Projet dbt Core (ETL)
  - 📂 **models/**
    - 📂 **staging/** — Données brutes nettoyées
    - 📂 **intermediate/** — Transformations intermédiaires *(vide actuellement)*
    - 📂 **marts/** — Modèles finaux — KPI & éligibilité

- 📂 **great_expectations/** — Tests de qualité des données
  - 📄 `run_ge_validations.py` — Script d'exécution des validations

- 📂 **data_generation/** — Scripts Python
  - Ingestion des données
  - Envoi des notifications Slack

- 📂 **data/** — Données sources simulées
  - 📂 **excel/** — Fichiers RH
  - 📂 **json/** — Données Strava simulées
    - 📂 **archive/** — Données déjà intégrées

- 📂 **powerbi/** — Fichiers Power BI

## Description des composants

### 🗄️ PostgreSQL
Base de données centrale du projet. Elle stocke :
- Les données RH des salariés
- Les activités sportives simulées 
- Les résultats des transformations dbt

### ⚙️ dbt Core (ETL)
Gère l'ensemble des transformations de données :
- **Staging** : Nettoyage et standardisation des données brutes
- **Marts** : Calcul de l'éligibilité aux avantages, KPI financiers

### 🔄 Kestra (Orchestration & Monitoring)
Orchestre et monitore l'ensemble des flux :
- Déclenchement automatique du pipeline ETL
- Surveillance de la volumétrie et de l'état d'exécution
- Envoi des notifications Slack lors de nouvelles activités

### ✅ Great Expectations (Qualité des données)
Documente et exécute les tests de cohérence :
- Distances non négatives
- Salaire cohérent
- Types d'activités dans une liste référentielle
- Distances cohérentes

### 📊 Power BI (Visualisation)
Dashboard de restitution des KPI :
- Coût total des avantages pour l'entreprise
- Nombre de salariés éligibles (prime sportive / jours bien-être)

## Variables d'environnement

Copiez `.env.example` en `.env` et renseignez les valeurs suivantes :

\```env
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=poc_sport
POSTGRES_USER=poc_user
POSTGRES_PASSWORD=poc_password

# Open Route Service
ORS_API_KEY=VotreClelApiOpenRouteService

# Slack
SLACK_TOKEN=VotreTokenSlack
SLACK_CHANNEL=#sport-entreprise

# LocalStack
LOCALSTACK_AUTH_TOKEN=VotreTokenPourLocalstackCommunity
\```

> ⚠️ **Ne jamais committer le fichier `.env`** — il est inclus dans le `.gitignore`.
