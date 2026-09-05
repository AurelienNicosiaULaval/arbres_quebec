# Références

- `frozen_sources.csv` : sources exactes de la version, URL et SHA-256.
- `source_manifest.csv` : ressources officielles disponibles pour des constructions ultérieures; leurs URL sont évolutives.
- `mrnf_field_inventory.csv` : champs et descriptions extraits du dictionnaire MRNF, avec son empreinte.
- `mrnf_species_codes.csv` : codes et noms de la feuille `ESSENCES`, y compris les codes agrégés.
- `species_taxonomy_crosswalk.csv` : résultat reproductible du rapprochement avec VASCAN 37.16. `exact_code` désigne un appariement automatique après normalisation, `reviewed` une revue documentaire consignée et `needs_review` une correspondance non résolue.
- `pedagogical_taxonomy_review.csv` : références et portée de la revue des quatre espèces pédagogiques.
- `age_source_codes.csv` : décodage officiel de `SOURCE_AGE`, extrait du dictionnaire figé.
- `species_code_exclusions.csv` : éventuelles exclusions explicites supplémentaires. Le fichier vide n'ajoute aucune exclusion; le pipeline détecte aussi les libellés agrégés et les mesures manquantes.

Les champs `quebec_status` sont repris de la table de distribution de VASCAN au
rang d'espèce. Une valeur vide n'indique pas l'absence au Québec : pour certains
taxons, la répartition du site VASCAN est calculée à partir des taxons inférieurs.
