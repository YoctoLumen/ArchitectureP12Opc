

with source as (
    select * from "poc_sport"."raw"."employees"
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
    
)

select * from renamed