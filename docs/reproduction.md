# Reproduire la version 1.0.0

## Utilisation pédagogique

Décompresser l'archive `arbres_quebec-v1.0.0.zip` et ouvrir `arbres_quebec.Rproj`
dans RStudio. Le petit jeu, ses dictionnaires et les deux rapports HTML sont
inclus. Exécuter `examples/01_explorer_les_arbres.R` pour reproduire le tableau
et le graphique. Les résultats sont écrits dans `outputs/`.

L'activité requiert `readr`, `dplyr` et `ggplot2`. La validation portable et le
rendu nécessitent aussi `tidyr`, `digest`, `jsonlite`, `lubridate`, `stringr`,
`knitr` et `rmarkdown`. Quarto est une application système, distincte des paquets R.

## Environnement enregistré

La livraison a été construite avec R 4.5.0. `renv.lock` consigne les versions
des dépendances; `validation/session_info.txt` consigne celles effectivement
chargées lors de la vérification source. Pour restaurer les paquets dans une
bibliothèque isolée depuis la racine du projet :

```r
install.packages("renv")
renv::restore(prompt = FALSE)
renv::activate()
```

La restauration peut nécessiter les bibliothèques système usuelles de `sf`,
`RSQLite` et `arrow`. L'utilisation du seul petit jeu n'en dépend pas.

## Validation portable

Depuis le terminal de RStudio, dans la racine du projet :

```bash
Rscript scripts/04_validate_release.R
Rscript examples/01_explorer_les_arbres.R
quarto render
```

La validation vérifie l'équilibre, les clés, les mesures, les dates, le
dictionnaire, la taxonomie et la concordance des empreintes avec la vérification
source enregistrée. Elle ne relit pas les sources MRNF en mode portable.
Les deux documents Quarto se reconstruisent avec les fichiers inclus.

## Reconstruction intégrale

La release contient trois fichiers sources inchangés : `PET5_GPKG.zip`,
`DICTIONNAIRE_PLACETTE.xlsx` et `vascan_dwca_v37.16.zip`. Le script de téléchargement
utilise ces copies figées et contrôle SHA-256; il refuse de remplacer un fichier
existant différent. Prévoir plusieurs gigaoctets d'espace de travail.

```bash
Rscript scripts/00_download_frozen_sources.R
Rscript scripts/03_build_species_taxonomy_crosswalk.R
OVERWRITE_CLEAN=true Rscript scripts/02_clean_botanical_data.R
Rscript scripts/04_validate_release.R --from-source
quarto render
```

Les paramètres de la version sont `ARBRES_QC_SOURCE=PET5`, `SMALL_N_SPECIES=4`,
`SMALL_N_PER_SPECIES=50`, `SMALL_SEED=20260625`, `MAX_ROWS_DEVELOPMENT=0`.
Ce sont les valeurs par défaut. Le tri par identifiant et le générateur aléatoire
sont explicites. Le journal d'exclusion doit couvrir exactement la table complète
moins les 200 arbres retenus.

Les URL courantes du MRNF dans `references/source_manifest.csv` servent à
préparer une future version. Elles ne remplacent pas les copies figées dans une
reconstruction de 1.0.0. Les voies PET4 et PEP ne font pas partie de cette livraison
validée. Toute mise à jour des données ou des règles de sélection exige une
nouvelle version et ses propres contrôles.

## Intégrité de l'archive

`checksums_repo.txt` répertorie les fichiers livrés et leurs empreintes SHA-256,
à l'exception du manifeste lui-même et des HTML reconstruits. Dans un terminal :

```bash
shasum -a 256 -c checksums_repo.txt
```

Les empreintes des pièces jointes à la release sont dans `SHA256SUMS.txt`.
Le script `scripts/05_package_release.R` assemble une archive autonome après
rendu; il refuse les fichiers de validation en échec ou un CSV différent de
celui vérifié depuis les sources.
