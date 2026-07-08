
CREATE DATABASE kestra OWNER poc_user;
CREATE ROLE readonly_user WITH LOGIN PASSWORD 'readonly_password';
CREATE ROLE etl_user WITH LOGIN PASSWORD 'etl_password';
GRANT ALL PRIVILEGES ON DATABASE kestra TO etl_user;
\c poc_sport;

CREATE SCHEMA IF NOT EXISTS raw;       -- Données brutes ingérées
CREATE SCHEMA IF NOT EXISTS staging;   -- Données nettoyées
CREATE SCHEMA IF NOT EXISTS intermediate; -- Données intermediaires
CREATE SCHEMA IF NOT EXISTS mart;      -- Données métier agrégées

-- Table des employés (données RH brutes)
CREATE TABLE IF NOT EXISTS raw.employees (
    id                      VARCHAR(50) PRIMARY KEY,
    nom                     VARCHAR(100) NOT NULL,
    prenom                  VARCHAR(100) NOT NULL,
    adresse                 TEXT NOT NULL,
    code_postal             VARCHAR(10),
    ville                   VARCHAR(100),
    salaire_brut_annuel     NUMERIC(12, 2),
    mode_transport_declare  VARCHAR(50),
    actif                   BOOLEAN DEFAULT TRUE,
    date_entree             DATE,
    inserted_at             TIMESTAMP DEFAULT NOW()
);

-- Table des activités Strava simulées (données brutes)
CREATE TABLE IF NOT EXISTS raw.activities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    id_salarie      VARCHAR(50) NOT NULL REFERENCES raw.employees(id),
    date_debut      TIMESTAMP NOT NULL,
    type            VARCHAR(50) NOT NULL,
    distance_m      INTEGER,           -- NULL si non pertinent (escalade, etc.)
    date_fin        TIMESTAMP,
    commentaire     TEXT,
    source          VARCHAR(20) DEFAULT 'simulation',  -- 'simulation' ou 'strava_api'
    inserted_at     TIMESTAMP DEFAULT NOW()
);

-- Table des distances domicile/bureau (résultats Google Maps)
CREATE TABLE IF NOT EXISTS raw.distances (
    id              SERIAL PRIMARY KEY,
    id_salarie      VARCHAR(50) NOT NULL REFERENCES raw.employees(id),
    distance_m      INTEGER NOT NULL,
    mode_transport  VARCHAR(50) NOT NULL,
    valide          BOOLEAN,
    motif_rejet     TEXT,
    calcule_le      TIMESTAMP DEFAULT NOW()
);


-- etl_user : lecture/écriture sur raw et staging, lecture sur mart
GRANT ALL PRIVILEGES ON DATABASE poc_sport TO etl_user;

GRANT CREATE ON SCHEMA staging TO etl_user;
GRANT CREATE ON SCHEMA mart TO etl_user;
GRANT CREATE ON SCHEMA intermediate TO etl_user;
GRANT CONNECT ON DATABASE poc_sport TO etl_user;

-- Droits sur les futures tables créées par dbt
ALTER USER etl_user CREATEDB;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA intermediate 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_user;

GRANT USAGE ON SCHEMA raw, staging, mart, intermediate TO etl_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA raw TO etl_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA staging TO etl_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA mart TO etl_user;

-- readonly_user : lecture seule sur mart (Power BI)
GRANT USAGE ON SCHEMA mart TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA mart TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA mart
    GRANT SELECT ON TABLES TO readonly_user;

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- Chiffrement données sensibles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Génération UUID

CREATE INDEX idx_activities_salarie ON raw.activities(id_salarie);
CREATE INDEX idx_activities_date ON raw.activities(date_debut);
CREATE INDEX idx_activities_type ON raw.activities(type);
CREATE INDEX idx_distances_salarie ON raw.distances(id_salarie);

DO $$ BEGIN RAISE NOTICE '✅ Initialisation PostgreSQL terminée !'; END $$;
