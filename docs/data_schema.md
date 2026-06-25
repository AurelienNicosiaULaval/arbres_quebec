# Schéma recommandé

## Unité statistique

`arbres_quebec.csv` contient une ligne par **arbre × campagne de mesure**. Cette définition fonctionne pour PET5/PET4 et demeure valide si PEP est ajouté plus tard.

Clés :

- `record_id` : ligne unique (`ID_ARBRE` dans PET, `ID_ARB_MES` dans PEP);
- `tree_id` : arbre stable (`ID_ARBRE`);
- `plot_measurement_id` : campagne de placette (`ID_PE` dans PET, `ID_PE_MES` dans PEP);
- `plot_id` : placette (`ID_PE`).

## Blocs de variables

### Identité et temps

`record_id`, `tree_id`, `plot_measurement_id`, `plot_id`, `survey_year`, `measurement_date`, `source_inventory`, `source_network`.

### Taxonomie

`species_code`, `species_fr`, `species_latin`, `genus`, `family`, `vascan_taxon_id`, `quebec_status`, `taxonomy_match_method`, `taxonomy_match_status`.

Les champs scientifiques restent manquants tant qu'un appariement revu n'existe pas. Le code MRNF et le nom français décodé restent toujours traçables.

### Mesures

- DHP : `diameter_mm` observé, `diameter_cm` converti;
- hauteur : `height_observed_m`, `height_estimated_m`, `height_m`, `height_source`;
- âge : `age_years`, `age_source_code`;
- contexte de cime : `canopy_stratum_code`, `canopy_stratum`;
- état : `vitality_code`, `vitality_status`;
- qualité/défoliation : variables sources conservées lorsqu'elles existent.

`crown_class` reste manquant dans la version initiale : `ETAGE_ARB` représente l'étage relatif de l'arbre et n'est pas renommé de façon trompeuse.

### Contexte spatial

`ecological_region_code`, `ecological_region`, `ecological_subregion_code`, `bioclimatic_domain_code`, `bioclimatic_domain`, `ecological_district_code`, `latitude`, `longitude`, `map_sheet`.

`region` administrative reste manquante sans jointure spatiale vers une couche administrative officielle. Elle ne doit pas être inférée du feuillet.

### Provenance et qualité

`measurement_source`, `source_file`, `source_file_sha256`, `source_table`, `source_variable_names`, `species_is_aggregate`, `data_quality_flag`, `observation_quality`, `notes`.

## Variables dérivées

| Variable | Définition | Justification | Mise en garde |
|---|---|---|---|
| `survey_year` | année de `measurement_date` | simplifie les analyses temporelles | reste NA si la date est inconnue |
| `diameter_cm` | `diameter_mm / 10` | unité pédagogique courante | ne modifie pas la mesure source |
| `height_observed_m` | `HAUT_ARBRE / 10` | unité pédagogique courante | sous-échantillon d'arbres d'étude |
| `height_estimated_m` | `HAUT_ESTI / 10` | rend l'estimation utilisable | ne jamais présenter comme observation |
| `height_m` | hauteur observée, sinon estimée | champ pratique pour certaines analyses | toujours utiliser avec `height_source` |
| `diameter_group` | classes fixes `<10`, `10–<20`, `20–<30`, `30–<40`, `≥40` cm | exercices de regroupement | classes didactiques, pas norme sylvicole |
| `height_group` | classes fixes `<5`, `5–<10`, `10–<15`, `15–<20`, `≥20` m | exercices de regroupement | classes didactiques |
| `age_class` | six classes fixes de 20 ans, puis `≥100` | tableaux croisés | ne remplace pas les classes officielles |
| `species_group` | valeur revue dans le crosswalk taxonomique | regrouper conifères, feuillus, autres | pas d'inférence depuis le code seul |
| `is_conifer` | booléen taxonomique revu | exercices binaires | NA si inconnu |
| `is_deciduous` | booléen taxonomique revu | exercices binaires | NA si inconnu |
| `basal_area_m2` | `π × (diameter_cm / 200)^2` | notion dendrométrique réelle | déterministe à partir du DHP; redondant en ACP |
| `observation_quality` | classe A/B/C/D ou contrôle requis selon provenance et complétude | rendre la qualité visible | classement documentaire, non validé comme score scientifique |

Le fichier `data_dictionary.csv` fournit la définition détaillée de chaque champ, son unité, son rôle, son origine, ses valeurs manquantes et ses règles de contrôle.
