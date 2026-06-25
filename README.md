# arbres_quebec

Pipeline reproductible pour construire un jeu de données pédagogique québécois d'arbres à partir des inventaires écoforestiers ouverts du ministère des Ressources naturelles et des Forêts (MRNF).

## Décision scientifique

Ce projet ne prétend pas reproduire les mesures florales de `iris`. Les sources forestières ne contiennent pas la longueur et la largeur des sépales ou pétales. Elles permettent toutefois un **équivalent botanique et dendrométrique** crédible : une ligne par arbre (ou par arbre et campagne de mesure), une espèce cible, des mesures réelles de diamètre, de hauteur et parfois d'âge, ainsi que le contexte de placette.

La source recommandée pour une première version est la **Placette-échantillon temporaire du cinquième inventaire (PET5)**. Elle évite la dépendance temporelle propre aux placettes permanentes et fournit une structure plus simple pour l'enseignement. La version pédagogique doit privilégier les arbres d'étude ayant une hauteur observée; les hauteurs estimées restent identifiées séparément dans la version complète.

## Ce dépôt ne contient pas de fausses observations

Les dossiers de données sont vides à l'origine. Les fichiers suivants sont produits seulement après téléchargement et exécution du pipeline :

- `data_clean/arbres_quebec.csv` : version complète harmonisée;
- `data_clean/arbres_quebec_small.csv` : sous-échantillon pédagogique équilibré;
- `data_clean/data_dictionary.csv` : dictionnaire livré avec la version construite;
- `data_clean/exclusion_log.csv` : exclusions de la petite version;
- `data_clean/validation_summary.csv` : contrôles structurés.

Aucune ligne synthétique ou imputée n'est fournie.

## Démarrage

### 1. Dépendances R

```r
install.packages(c(
  "arrow", "cli", "curl", "DBI", "dbplyr", "digest", "dplyr",
  "fs", "ggplot2", "janitor", "knitr", "lubridate", "purrr", "readr",
  "readxl", "rlang", "RSQLite", "scales", "sf", "stringr",
  "tibble", "tidyr"
))
```

`terra` est utile pour des traitements spatiaux complémentaires, mais n'est pas requis par le pipeline initial.

### 2. Collecte

Le téléchargement du GeoPackage PET5 est désactivé par défaut, car l'archive est volumineuse. Pour autoriser les gros téléchargements :

```bash
DOWNLOAD_LARGE_FILES=true Rscript scripts/01_collect_botanical_sources.R
```

Sans cette variable, le script télécharge seulement les petits documents et produit des instructions de téléchargement manuel. Il ne remplace jamais un fichier brut existant.

### 3. Nettoyage

```bash
ARBRES_QC_SOURCE=PET5 Rscript scripts/02_clean_botanical_data.R
```

Variables d'environnement utiles :

```bash
SMALL_N_SPECIES=4 SMALL_N_PER_SPECIES=50 SMALL_SEED=20260625 \
OVERWRITE_CLEAN=false Rscript scripts/02_clean_botanical_data.R
```

### 4. Validation

```bash
quarto render docs/validation_report.qmd
```

## Principes de construction

- Les unités sources sont conservées dans les champs bruts et converties explicitement : DHP en millimètres vers centimètres; hauteur en décimètres vers mètres.
- `height_observed_m` et `height_estimated_m` ne sont jamais confondus silencieusement.
- Les valeurs manquantes restent manquantes; le pipeline n'effectue aucune imputation.
- Les anomalies sont signalées plutôt que supprimées dans la version complète.
- La sélection de la petite version est déterministe, déclarée et journalisée.
- Les noms scientifiques, genres et familles exigent une correspondance taxonomique revue. Un gabarit est fourni dans `references/species_taxonomy_crosswalk.csv`.
- Les séparations apprentissage/test doivent être groupées par placette afin de réduire la fuite d'information.

## Structure

- `data_raw/` : fichiers téléchargés, inchangés et accompagnés de sommes SHA-256.
- `data_intermediate/` : extractions et tables de travail régénérables.
- `data_clean/` : produits analytiques finaux.
- `R/` : fonctions réutilisables.
- `scripts/` : scripts ordonnés de collecte et de nettoyage.
- `docs/` : diagnostic, activités pédagogiques et rapport Quarto.
- `references/` : manifeste des sources, gabarit taxonomique et décisions documentaires.
- `logs/` : journaux de collecte et d'exécution.

## Licences

Le code du dépôt est sous licence MIT. Les données sources conservent leur licence propre. Les données MRNF et celles de Montréal sont annoncées sous CC BY 4.0; VASCAN est sous CC0 1.0. Voir `DATA_LICENSES.md`. Le dépôt ne relicencie pas les données de tiers.

## Citation

Voir `CITATION.cff`. Pour une publication ou un travail étudiant, citer également les jeux sources, leur date d'accès, leur version ou empreinte SHA-256, et VASCAN lorsqu'il est utilisé.
