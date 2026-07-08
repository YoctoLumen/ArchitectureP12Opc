{{ config(materialized='incremental', unique_key='activity_id') }}

with source as (
    select * from {{ source('raw', 'activities') }}
),

renamed as (
    select
        id                                          as activity_id,
        id_salarie                                  as employee_id,
        type                                        as type_activite,
        distance_m                                  as distance_m,
        round(distance_m / 1000.0, 2)              as distance_km,
        date_debut                                  as date_debut,
        date_fin                                    as date_fin,
        extract(epoch from (date_fin - date_debut)) / 60
                                                    as duree_minutes,
        commentaire                                 as commentaire,
        source                                      as source,
        inserted_at                                 as updated_at
    from source
    where date_debut is not null
    {% if is_incremental() %}
        and inserted_at > (select max(updated_at) from {{ this }})
    {% endif %}
)

select * from renamed
