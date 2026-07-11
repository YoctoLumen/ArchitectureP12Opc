

with employees as (

    select * from "poc_sport"."staging"."stg_employees"

),

activities as (

    select * from "poc_sport"."staging"."stg_activities"

),

activites_par_salarie as (

    select
        employee_id,
        count(*)                            as nb_activites_annee,
        min(date_debut)                     as premiere_activite,
        max(date_debut)                     as derniere_activite,
        count(*) filter (
            where type_activite = 'Course à pied'
        )                                   as nb_course,
        count(*) filter (
            where type_activite = 'Randonnée'
        )                                   as nb_randonnee,
        count(*) filter (
            where type_activite = 'Vélo'
        )                                   as nb_velo,
        round(sum(distance_km), 2)          as distance_totale_km

    from activities
    where
        extract(year from date_debut) = extract(year from current_date)
        and date_fin is not null

    group by employee_id

),

joined as (

    select

        e.employee_id,
        e.nom,
        e.prenom,
        e.date_embauche,

        coalesce(a.nb_activites_annee, 0)   as nb_activites_annee,
        coalesce(a.nb_course, 0)            as nb_course,
        coalesce(a.nb_randonnee, 0)         as nb_randonnee,
        coalesce(a.nb_velo, 0)             as nb_velo,
        coalesce(a.distance_totale_km, 0)   as distance_totale_km,
        a.premiere_activite,
        a.derniere_activite,

        15                                  as seuil_activites_requis,

        case
            when a.employee_id is null
                then false
            when a.nb_activites_annee >= 15
                then true
            else false
        end                                 as est_eligible_journees,

        case
            when a.employee_id is null
                then 0
            when a.nb_activites_annee >= 15
                then 5
            else 0
        end                                 as nb_journees_accordees,

        case
            when a.employee_id is null
                then 'Aucune activité enregistrée cette année'
            when a.nb_activites_annee < 15
                then concat(
                    'Nombre d''activités insuffisant : ',
                    a.nb_activites_annee,
                    '/15 requises (manque ',
                    15 - a.nb_activites_annee,
                    ' activité(s))'
                )
            else null
        end                                 as motif_ineligibilite,

        extract(year from current_date)     as annee_reference

    from employees e
    left join activites_par_salarie a
        on e.employee_id = a.employee_id

)

select * from joined