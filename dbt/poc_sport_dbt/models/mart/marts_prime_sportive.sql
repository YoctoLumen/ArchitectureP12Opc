{{ config(materialized='table') }}

with employees as (
    select * from {{ ref('stg_employees') }}
),

distances as (
    select * from {{ ref('stg_distances') }}
),

latest_distances as (
    select distinct on (employee_id)
        employee_id,
        distance_domicile_travail_m,
        distance_domicile_travail_km,
        mode_transport,
        motif_rejet,
        calcule_le
    from distances
    order by employee_id, calcule_le desc
),

joined as (
    select
        e.employee_id,
        e.nom,
        e.prenom,
        e.adresse,
        e.code_postal,
        e.ville,
        e.salaire_brut_annuel,
        e.mode_transport_declare,
        e.date_embauche,
        d.distance_domicile_travail_m,
        d.distance_domicile_travail_km,
        d.mode_transport                        as mode_transport_calcule,
        d.calcule_le                            as distance_calculee_le,

        case
            when d.employee_id is null
                then false
            when e.mode_transport_declare in ('Marche/running')
                and d.distance_domicile_travail_km <= 15
                then true
            when e.mode_transport_declare in ('Vélo/Trottinette/Autres')
                and d.distance_domicile_travail_km <= 25
                then true
            else false
        end                                     as est_eligible_prime,

        case
            when d.employee_id is null
                then 0
            when e.mode_transport_declare in ('Marche/running')
                and d.distance_domicile_travail_km <= 15
                then round(e.salaire_brut_annuel * 0.05, 2)
            when e.mode_transport_declare in ('Vélo/Trottinette/Autres')
                and d.distance_domicile_travail_km <= 25
                then round(e.salaire_brut_annuel * 0.05, 2)
            else 0
        end                                     as montant_prime,

        case
            when d.employee_id is null
                then 'Aucune distance valide calculée pour ce salarié'
            when e.mode_transport_declare not in ('Vélo/Trottinette/Autres', 'Marche/running')
                then 'Mode de déplacement non éligible'
            when e.mode_transport_declare in ('Marche/running')
                and d.distance_domicile_travail_km > 15
                then 'Mode de déplacement éligible mais distance incohérent ( superieur à 15 km pour de la marche/running)'
            when e.mode_transport_declare in ('Vélo/Trottinette/Autres')
                and d.distance_domicile_travail_km > 25
                then 'Mode de déplacement éligible mais distance incohérent ( superieur à 25 km pour du vélo/trottinette ou autre)'
            else null
        end                                     as motif_ineligibilite

    from employees e
    left join latest_distances d
        on e.employee_id = d.employee_id
)

select * from joined
