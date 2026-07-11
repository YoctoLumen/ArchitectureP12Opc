
  
    

  create  table "poc_sport"."mart"."marts_avantages_salaries__dbt_tmp"
  
  
    as
  
  (
    

with prime as (
    select * from "poc_sport"."mart"."marts_prime_sportive"
),

bienetre as (
    select * from "poc_sport"."mart"."marts_journees_bienetre"
)

select
    p.employee_id,
    p.nom,
    p.prenom,
    p.salaire_brut_annuel,
    p.mode_transport_declare,
    p.est_eligible_prime,
    p.montant_prime,
    p.motif_ineligibilite       as motif_ineligibilite_prime,
    b.nb_activites_annee,
    b.distance_totale_km,
    b.est_eligible_journees,
    b.nb_journees_accordees,
    b.motif_ineligibilite       as motif_ineligibilite_bienetre,
    p.montant_prime             as cout_prime_sportive,
    case
        when b.est_eligible_journees
            then round((p.salaire_brut_annuel / 218) * 5, 2)
        else 0
    end                         as cout_journees_bienetre,

    b.annee_reference

from prime p
left join bienetre b
    on p.employee_id = b.employee_id
  );
  