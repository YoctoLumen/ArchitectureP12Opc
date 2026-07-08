

with source as (
    select * from "poc_sport"."raw"."distances"
),

renamed as (
    select
        id                                          as distance_id,
        id_salarie                                  as employee_id,
        distance_m                                  as distance_domicile_travail_m,
        round(distance_m / 1000.0, 2)              as distance_domicile_travail_km,
        mode_transport                              as mode_transport,
        valide                                      as est_valide,
        motif_rejet                                 as motif_rejet,
        calcule_le                                  as calcule_le
    from source
    where valide = true
    
)

select * from renamed