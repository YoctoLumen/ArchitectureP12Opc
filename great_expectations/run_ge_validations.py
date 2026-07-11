import os
import great_expectations as gx


CONNECTION_STRING = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

context = gx.get_context()
datasource = context.sources.add_or_update_sql(
    name="poc_sport_postgres",
    connection_string=CONNECTION_STRING
)

SUITES = {
    "raw_activities_suite": {
        "schema": "raw", "table": "activities",
        "not_null": ["id", "id_salarie", "date_debut", "type"],
        "between":  [("distance_m", 0, None, 0.95)],
        "in_set":   [
            ("type", ["Workout", "Run", "Hike", "Swim", "Walk", "Ride"]),
            ("source", ["simulation", "strava_api"]),
        ],
    },
    "raw_employees_suite": {
        "schema": "raw", "table": "employees",
        "not_null": ["id", "nom", "prenom", "adresse", "salaire_brut_annuel"],
        "unique":   ["id"],
        "between":  [("salaire_brut_annuel", 0, 500000, 1.0)],
        "in_set":   [
            ("mode_transport_declare", ["Marche/running", "Vélo/Trottinette/Autres",
                                        "véhicule thermique/électrique", "Transports en commun"]),
        ],
    },
    "mart_prime_sportive_actifs_suite": {
        "query": """
            SELECT * FROM mart.marts_prime_sportive
            WHERE mode_transport_declare IN ('Marche/running', 'Vélo/Trottinette/Autres')
        """,
        "between": [
            ("distance_domicile_travail_km", 0, 200, 0.99),
        ],
    },
}

def build_and_run(suite_name: str, config: dict) -> bool:
    suite = context.add_or_update_expectation_suite(suite_name)

    if "query" in config:
        asset = datasource.add_query_asset(
            name=f"{suite_name}_asset",
            query=config["query"]
        )
    else:
        asset = datasource.add_table_asset(
            name=f"{config['schema']}_{config['table']}",
            schema_name=config["schema"],
            table_name=config["table"]
        )
    batch_request = asset.build_batch_request()

    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=suite_name,
    )

    for col in config.get("not_null", []):
        validator.expect_column_values_to_not_be_null(col)

    for col in config.get("unique", []):
        validator.expect_column_values_to_be_unique(col)

    for col, min_v, max_v, mostly in config.get("between", []):
        kwargs = {"column": col, "min_value": min_v, "mostly": mostly}
        if max_v is not None:
            kwargs["max_value"] = max_v
        validator.expect_column_values_to_be_between(**kwargs)

    for col, values in config.get("in_set", []):
        validator.expect_column_values_to_be_in_set(col, values)

    result  = validator.validate()
    success = result["success"]
    status  = "✅" if success else "❌"
    print(f"{status} {suite_name}")

    if not success:
        for r in result["results"]:
            if not r["success"]:
                print(f"   ⚠️  {r['expectation_config']['expectation_type']} "
                      f"— colonne : {r['expectation_config']['kwargs'].get('column', 'N/A')}")
    return success


if __name__ == "__main__":
    print("\n🔍 Démarrage des validations Great Expectations...\n")

    results = {name: build_and_run(name, cfg) for name, cfg in SUITES.items()}

    total, success = len(results), sum(results.values())
    print(f"\n{'='*40}")
    print(f"📋 RÉSUMÉ : {success}/{total} suites validées")
    if success < total:
        print("⚠️  Vérifier les données en erreur !")
        # exit(1)
    else:
        print("🎉 Toutes les validations sont passées !")
    print(f"{'='*40}\n")