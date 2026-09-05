# Arbres du Québec

Un jeu de données pour enseigner la statistique et R avec des arbres mesurés au Québec. La version pédagogique contient 200 arbres, soit 50 de chacune de quatre espèces : bouleau à papier, épinette noire, érable rouge et sapin baumier. Elle propose une alternative forestière à `iris`, avec des mesures de diamètre et de hauteur et une provenance vérifiable pour chaque ligne.

Version 1.0.0, 5 septembre 2026.

## Télécharger et commencer

1. [Télécharger le petit jeu et l'activité R](https://github.com/AurelienNicosiaULaval/arbres_quebec/releases/download/v1.0.0/arbres_quebec-v1.0.0.zip).
2. Décompresser l'archive et ouvrir `arbres_quebec.Rproj` dans RStudio.
3. Ouvrir `docs/premiers_pas.html` pour suivre l'activité, ou exécuter `examples/01_explorer_les_arbres.R`.

[CSV pédagogique seul](https://raw.githubusercontent.com/AurelienNicosiaULaval/arbres_quebec/v1.0.0/data_clean/arbres_quebec_small.csv) · [Dictionnaire des 21 variables](data_clean/arbres_quebec_small_dictionary.csv) · [Tous les fichiers de la version](https://github.com/AurelienNicosiaULaval/arbres_quebec/releases/tag/v1.0.0)

```r
# Installation à effectuer une seule fois.
install.packages(c("readr", "dplyr", "ggplot2"))

library(readr)
library(dplyr)
library(ggplot2)

arbres <- read_csv(
  "data_clean/arbres_quebec_small.csv",
  col_types = cols(.default = col_guess(), plot_id = col_character(),
                   tree_id = col_character(), record_id = col_character())
)

arbres |> count(species)

ggplot(arbres, aes(diameter_cm, height_m, colour = species)) +
  geom_point() +
  labs(x = "Diamètre (cm)", y = "Hauteur observée (m)", colour = "Espèce") +
  theme_minimal()
```

## Contenu

| Fichier | Usage |
|---|---|
| `data_clean/arbres_quebec_small.csv` | 200 arbres et 21 variables, directement utilisables dans R |
| `data_clean/arbres_quebec_small_dictionary.csv` | Définition et unités des 21 variables |
| `data_clean/arbres_quebec_small_provenance.csv` | Valeurs sources et identifiants des 200 arbres |
| `data_clean/small_sampling_manifest.csv` | Espèces sélectionnées, effectifs et graine |
| `docs/premiers_pas.html` | Activité exécutée : importation, tableaux, graphique et exercices |
| `docs/validation_report.html` | Résultats des contrôles et limites d'utilisation |
| `validation/` | Contrôles, profils, vérification source et environnement R |
| `arbres_quebec.parquet`, dans la release | Table complète harmonisée : 1 961 039 observations et 41 901 placettes |

Les HTML sont inclus dans l'archive pédagogique. La table complète et les sources volumineuses sont des fichiers de la release, hors de l'historique Git.

## Construction et portée

La source est le jeu PET5 du ministère des Ressources naturelles et des Forêts (MRNF), téléchargé le 25 juin 2026. Les fichiers originaux sont figés par leurs empreintes SHA-256. La taxonomie est rapprochée de VASCAN 37.16. Les quatre espèces pédagogiques ont en plus une revue documentaire explicitée dans [`references/pedagogical_taxonomy_review.csv`](references/pedagogical_taxonomy_review.csv).

La sélection utilise les arbres ayant une essence non agrégée, un diamètre positif et une hauteur observée positive. Après classement stable par identifiant, un arbre est tiré par couple espèce-placette. Les quatre espèces avec le plus de placettes admissibles sont retenues, puis 50 arbres sont tirés par espèce. La graine est `20260625`; l'environnement R est enregistré. Chaque autre observation figure dans le journal d'exclusion de la construction.

Cette sélection est équilibrée pour l'enseignement. Elle ne fournit pas les proportions des espèces, ni des moyennes représentatives de tous les arbres du Québec. Les mesures florales de `iris` ne sont pas reproduites.

## Précautions pour l'analyse

- `height_m` est toujours observée dans le petit jeu. Dans la table complète, consulter `height_source` pour distinguer hauteurs observées et estimées.
- Les âges manquants restent manquants. L'âge publié peut provenir d'une carotte complète ou incomplète, à un niveau de lecture donné; il ne représente pas nécessairement l'âge total de l'arbre.
- `basal_area_m2` est une fonction déterministe du diamètre. Ne pas la compter comme une mesure indépendante supplémentaire dans une ACP.
- Les régions écologiques ne sont pas des régions administratives. Le petit jeu n'est pas équilibré par région ni par année.
- Pour la classification, exclure les noms, codes, genres, familles et identifiants des prédicteurs. Grouper les partitions par `plot_id`; une extension à d'autres régions demande une validation spatiale adaptée.
- La table complète conserve les codes non résolus et les anomalies signalées. `exact_code` désigne un appariement automatique; `reviewed` une revue documentaire. La revue de livraison porte sur les quatre espèces du petit jeu.

## Vérifier ou reconstruire

Les commandes et les deux niveaux de validation, portable et depuis les sources, sont décrits dans [`docs/reproduction.md`](docs/reproduction.md). La reconstruction intégrale nécessite plusieurs gigaoctets d'espace de travail. Le petit jeu peut être utilisé sans télécharger ces sources.

Le dépôt utilise SSH :

```bash
git clone git@github.com:AurelienNicosiaULaval/arbres_quebec.git
```

## Sources, licence et citation

MRNF (2018), [Placette-échantillon temporaire du cinquième inventaire](https://www.donneesquebec.ca/recherche/dataset/placettes-echantillons-temporaires-du-cinquieme-inventaire), extraction du 25 juin 2026, CC BY 4.0. Brouillet et al. (2010+), [VASCAN, version 37.16](https://data.canadensys.net/ipt/resource?r=vascan&v=37.16), CC0 1.0. Les transformations et la sélection pédagogique sont celles de ce dépôt.

Le code est sous MIT; les données MRNF et leurs adaptations sont sous CC BY 4.0. Voir [`DATA_LICENSES.md`](DATA_LICENSES.md) et [`CITATION.cff`](CITATION.cff).
