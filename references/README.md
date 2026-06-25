# Références versionnées

- `source_manifest.csv` décrit les ressources candidates et leur emplacement local.
- `species_taxonomy_crosswalk.csv` doit être rempli et revu avant publication des noms scientifiques, genres, familles et groupes feuillus/résineux.
- `species_code_exclusions.csv` documente les codes agrégés, inconnus ou non admissibles comme classes de la petite version.

Le pipeline n'effectue pas de correspondance taxonomique floue silencieuse. Une ligne sans appariement revu conserve ses codes et noms français sources, tandis que les champs taxonomiques restent manquants.
- `mrnf_field_inventory.csv` est une extraction traçable des feuilles PEP, PET4 et PET5 du dictionnaire officiel inspecté; chaque ligne porte l'empreinte SHA-256 du XLSX.
- `mrnf_species_codes.csv` est l'extraction des codes et noms français de la feuille `ESSENCES`; elle contient aussi des codes non spécifiques, qui ne doivent pas être assimilés automatiquement à des espèces biologiques.
