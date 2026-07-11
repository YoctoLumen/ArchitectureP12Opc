{{ config(materialized='incremental', unique_key='employee_id') }}

with source as (
    select * from {{ source('raw', 'employees') }}
),

renamed as (
    select
        id                                          as employee_id,
        nom                                         as nom,
        prenom                                      as prenom,
        adresse                                     as adresse,
        code_postal                                 as code_postal,
        ville                                       as ville,
        salaire_brut_annuel                         as salaire_brut_annuel,
        mode_transport_declare                      as mode_transport_declare,
        actif                                       as est_actif,
        date_embauche                               as date_embauche,
        inserted_at                                 as updated_at
    from source
    where actif = true
    {% if is_incremental() %}
        and inserted_at > (
            select max_inserted
            from (select max(updated_at) as max_inserted from {{ this }}) as sub
        )
    {% endif %}
)

select * from renamed
