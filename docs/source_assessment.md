# Diagnostic de faisabilité et recommandation

Date d'évaluation : 2026-06-25

## Conclusion

Un équivalent floral exact de `iris` n'est pas réalisable à partir des sources prioritaires : aucune ne fournit des mesures homologues de sépales et de pétales sur plusieurs espèces québécoises. En revanche, un **équivalent botanique forestier** est réalisable avec nettoyage et documentation : une observation par arbre, une espèce cible, des mesures dendrométriques réelles, une placette, une date et un contexte écologique.

**Recommandation principale : PET5**, avec deux produits :

1. `arbres_quebec.csv` : tous les arbres admissibles de PET5, sans suppression silencieuse, avec séparation entre hauteur observée et hauteur estimée;
2. `arbres_quebec_small.csv` : arbres d'étude ayant DHP et hauteur observés, quatre espèces sélectionnées après comptage, échantillonnage équilibré et déterministe.

**Recommandation secondaire : PEP** pour un module longitudinal distinct sur la croissance, la dépendance entre mesures et les modèles mixtes. Ne pas mélanger naïvement plusieurs mesures du même arbre dans des partitions apprentissage/test.

## Sources vérifiées

| Option | Formats | Structure utile | Espèce | Français | Latin / genre / famille | DHP individuel | Hauteur | Âge | Placette | Localisation | Date | Extraction | Verdict |
|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|
| PEP — placettes permanentes | GPKG, XLSX, PDF | `PLACETTE`, `PLACETTE_MES`, `DENDRO_ARBRES`, `DENDRO_ARBRES_ETUDES`, `CLASSI_ECO_PE` | oui, code | oui, dictionnaire | non dans le dictionnaire MRNF; jointure externe | oui | observée sur arbres d'étude; estimée sur davantage d'arbres | arbres d'étude | oui, mesures répétées | latitude/longitude | `DATE_SOND` par mesure | élevée : modèle relationnel et mesures répétées | faisable avec nettoyage; excellent longitudinal |
| PET5 — placettes temporaires, 5e inventaire | GPKG, XLSX, PDF | `PLACETTE`, `DENDRO_ARBRES`, `DENDRO_ARBRES_ETUDES`, `CLASSI_ECO_PE` | oui, code | oui, dictionnaire | non dans le dictionnaire MRNF; jointure externe | oui | hauteur de trois arbres d'étude; hauteur estimée dans la table générale | arbres d'étude | oui | latitude/longitude | `DATE_SOND` | moyenne à élevée : fichier volumineux, jointures simples | **meilleur choix initial** |
| PET4 — placettes temporaires, 4e inventaire | GPKG, XLSX, PDF | tables analogues à PET5 | oui, code | oui, dictionnaire | non dans le dictionnaire MRNF; jointure externe | oui | observée sur arbres d'étude et estimée ailleurs | arbres d'étude | oui | latitude/longitude | `DATE_SOND`; 2004–2018 | élevée : archive très volumineuse | faisable; bonne cohorte historique figée |
| Arbres publics de Montréal | CSV, PDF | table plate d'arbres municipaux; historique DHP séparé | oui | oui | nom latin fourni; genre dérivable | oui | non | non; date de plantation parfois disponible, sans équivalence certaine avec l'âge biologique | non, mais emplacement municipal | coordonnées et adresse | date de relevé DHP | faible à moyenne | faisable seulement partiellement pour l'objectif forestier |
| VASCAN | DwC-A, métadonnées | taxons, noms acceptés, vernaculaires, classification, présence provinciale | autorité taxonomique | oui | oui | non | non | non | non | statut de répartition, pas point d'arbre | version de publication | moyenne : archive Darwin Core et appariement à revoir | source complémentaire, pas source de mesures |

## Champs confirmés dans le dictionnaire MRNF

### PET5

- `PLACETTE` : `ID_PE`, `TYPE_PE`, `DIMENSION`, `FEUILLET`, `LATITUDE`, `LONGITUDE`, `DATE_SOND`.
- `DENDRO_ARBRES` : `ID_ARBRE`, `ETAT`, `ESSENCE`, `DHP`, `CL_DEFOL`, `CL_QUAL`, `HAUT_ARBRE`, `ETAGE_ARB`, `AGE`, `HAUT_ESTI`, `ST_HA`, `VMB_HA` et variables de biomasse/carbone.
- `DENDRO_ARBRES_ETUDES` : sélection d'arbres avec `DHP`, `HAUT_ARBRE`, `AGE` et métadonnées de mesure.
- `CLASSI_ECO_PE` : `ZONE_VEG`, `SZONE_VEG`, `DOM_BIO`, `SDOM_BIO`, `REG_ECO`, `SREG_ECO`, `UPAYS_REG`, `DIS_ECO`.

### PEP

- `PLACETTE` : `ID_PE`, `RESEAU`, `LATITUDE`, `LONGITUDE`, statut et dernière campagne.
- `PLACETTE_MES` : `ID_PE_MES`, numéro de mesure, date de sondage et statut.
- `DENDRO_ARBRES` : `ID_ARB_MES`, `ID_ARBRE`, `ETAT`, `ESSENCE`, `DHP`, classes de qualité/défoliation, `HAUT_ESTI`, surface terrière et volume.
- `DENDRO_ARBRES_ETUDES` : hauteur observée, âge et méthode de sélection pour les arbres d'étude.
- Clé de jointure de campagne : `ID_PE_MES`; clé de l'arbre mesuré : `ID_ARB_MES`.

### Unités à convertir

- `DHP` : millimètres; `diameter_cm = DHP / 10`.
- `HAUT_ARBRE` et `HAUT_ESTI` : décimètres; hauteur en mètres obtenue par division par 10.
- `ST_TIGE`, lorsqu'elle existe : centimètres carrés; conversion en mètres carrés par division par 10 000.

## Comparaison qualitative

| Critère | PEP | PET5 | PET4 | Montréal |
|---|---|---|---|---|
| Proximité fonctionnelle avec `iris` | moyenne : individus et espèces, mais répétitions | **élevée pour un analogue forestier** | élevée pour un analogue forestier | moyenne : table simple, une seule mesure biologique principale |
| Richesse biologique | très élevée | très élevée | très élevée | moyenne, flore urbaine plantée |
| Qualité des mesures | élevée, avec changement possible de protocoles | élevée; distinguer observé/estimé | élevée; documentation historique | bonne pour le DHP, couverture spatiale inégale |
| Facilité d'accès | moyenne | moyenne; archive volumineuse | faible à moyenne; archive très volumineuse | élevée, CSV |
| Taille | grande, plus de 12 000 placettes et mesures répétées | très grande | très grande | grande mais table plate |
| Potentiel pédagogique | croissance, longitudinal, modèles mixtes | classification, ACP, kNN, contexte spatial | mêmes usages avec perspective historique | nettoyage simple, données urbaines, biais de gestion |
| Risque principal | fuite d'information entre campagnes et arbres | arbres d'étude non aléatoires; hauteur estimée | ancienneté et sélection des arbres d'étude | biais urbain, absence de hauteur/âge, localisation parfois imprécise |
| Recommandation | module avancé séparé | **source principale** | solution de repli ou cohorte historique | option alternative partielle |

## Pourquoi PET5 est préférable pour la première version

- Une placette temporaire représente une campagne plutôt qu'une série de mesures répétées : le modèle de données est plus proche d'une table pédagogique classique.
- Chaque arbre possède une essence et un DHP; certains arbres d'étude possèdent une hauteur et un âge observés.
- Les placettes sont reliables à des régions écologiques et à des coordonnées.
- La version actuelle permet de documenter la période à partir de 2017.
- Les limites restent enseignables : plan d'échantillonnage en grappes, classes déséquilibrées, mesures manquantes non aléatoires, estimation de hauteur et variation spatiale.

## Limites pédagogiques à rendre visibles

1. **Ce n'est pas un échantillon aléatoire simple d'arbres du Québec.** Les arbres sont regroupés en placettes et suivent un protocole d'inventaire.
2. **La hauteur observée et l'âge sont issus d'un sous-échantillon d'arbres d'étude.** Une analyse fondée sur eux décrit ce sous-échantillon.
3. **La surface terrière est déterministe à partir du DHP.** Elle ne doit pas être traitée comme une mesure indépendante dans une ACP avec le DHP sans discuter la colinéarité parfaite.
4. **L'espèce peut être confondue avec la région, l'année ou le type de peuplement.** Une classification très précise ne prouve pas que la morphologie seule identifie l'espèce.
5. **La validation doit être groupée par placette.** Une séparation aléatoire ligne par ligne surestime probablement la performance.
6. **Les valeurs manquantes peuvent être informatives.** L'absence de hauteur ne correspond pas nécessairement à une erreur; elle peut refléter le protocole de sélection.
7. **Le dictionnaire des essences contient des codes agrégés ou indéterminés.** Ils doivent être conservés et signalés dans la version complète, puis exclus explicitement de la cible pédagogique.
8. **La taxonomie évolue.** Les noms latins doivent porter une source, une version et un statut d'appariement.

## Recommandation de produit

### Version complète

Nom : `arbres_quebec.csv`.

Unité statistique recommandée : arbre × campagne de mesure. Pour PET5, chaque arbre apparaît normalement dans une seule campagne; pour une future version PEP, conserver explicitement `tree_id`, `plot_measurement_id` et `measurement_date`.

Inclure toutes les lignes pouvant être reliées à une placette. Ne pas éliminer les diamètres extrêmes ou les codes d'essence non spécifiques; ajouter plutôt des indicateurs de qualité. Conserver séparément les mesures observées et estimées.

### Version pédagogique

Nom : `arbres_quebec_small.csv`.

Unité statistique : un arbre d'étude PET5. Règle proposée :

1. garder les lignes ayant une essence non agrégée, un DHP positif et une hauteur **observée** positive;
2. prendre au plus un arbre par combinaison espèce–placette avant de calculer les fréquences;
3. sélectionner les quatre espèces ayant le plus grand nombre de placettes admissibles, avec bris d'égalité par code d'essence;
4. fixer `n = min(50, plus petit effectif admissible des quatre espèces)`;
5. échantillonner `n` arbres par espèce avec graine `20260625`;
6. conserver `plot_id` dans le fichier pour permettre une validation groupée;
7. écrire toutes les exclusions et les effectifs à chaque étape.

Cette règle équilibre les classes sans choisir « les plus beaux » arbres. Elle impose néanmoins une analyse en cas complets pour les deux mesures principales; cette restriction doit être publiée comme une sélection du sous-échantillon d'arbres d'étude.

Variables analytiques recommandées :

- cible : `species`;
- numériques principales : `diameter_cm`, `height_m`, `age_years` lorsque disponible;
- catégorielle optionnelle : `canopy_stratum`;
- métadonnées à ne pas utiliser automatiquement comme prédicteurs : `plot_id`, `ecological_region`, `survey_year`;
- variable didactique calculable : `basal_area_m2`, mais à retirer de l'ACP et de la classification lorsque `diameter_cm` est déjà utilisé.
