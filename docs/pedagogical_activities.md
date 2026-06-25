# Activités pédagogiques proposées

## 1. Portrait descriptif des espèces

**Niveau : STT-1100 et cours R.**

Calculer effectifs, moyenne, médiane, écart-type, quantiles et taux de valeurs manquantes par espèce. Comparer résultats bruts et résultats pondérés ou groupés par placette. Introduire la différence entre unité observée et unité d'échantillonnage.

## 2. Diamètre en fonction de la hauteur

**Niveau : STT-1100, cours R et science des données.**

Tracer nuages de points, facettes par espèce et lissages. Distinguer hauteur observée et estimée. Examiner l'hétéroscédasticité et les effets de région. Ne pas conclure à une relation causale à partir d'un graphique transversal.

## 3. Analyse en composantes principales

**Niveau : STT-2200 et science des données.**

Standardiser les mesures numériques, traiter l'âge manquant par une stratégie déclarée ou limiter l'analyse à un sous-échantillon. Exclure `basal_area_m2` si `diameter_cm` est présent afin d'éviter une variable presque parfaitement redondante. Interpréter charges, individus et séparation des espèces.

## 4. Classification supervisée de l'espèce

**Niveau : STT-2200 et science des données.**

Construire une référence simple, par exemple arbre de décision ou régression multinomiale. Séparer entraînement et test par `plot_id`. Comparer une stratégie morphologique seule à une stratégie ajoutant la région; discuter la confusion écologique et la généralisation hors région.

## 5. k plus proches voisins

**Niveau : STT-2200, cours R avancé et science des données.**

Centrer-réduire les variables, sélectionner `k` par validation croisée groupée par placette et produire matrice de confusion, rappel par classe et exactitude équilibrée. Montrer l'effet de l'échelle des variables.

## 6. Analyse discriminante

**Niveau : STT-2200 et projet avancé.**

Comparer LDA et QDA, vérifier approximativement les hypothèses de covariance et de normalité, puis évaluer avec groupes de placettes. Examiner les frontières de décision et les espèces fréquemment confondues.

## 7. Clustering non supervisé

**Niveau : STT-2200 et science des données.**

Appliquer k-means ou classification hiérarchique aux mesures standardisées sans utiliser l'espèce. Comparer les groupes aux espèces au moyen d'un tableau de contingence et d'un indice ajusté. Discuter pourquoi des groupes morphologiques ne coïncident pas nécessairement avec la taxonomie.

## 8. Comparaison critique avec `iris`

**Niveau : tous les niveaux; approfondissement en projet avancé.**

Comparer plan d'échantillonnage, équilibre des classes, indépendance, valeurs manquantes, provenance, unités, variables dérivées, biais géographique et stabilité taxonomique. Demander aux étudiants de préciser ce qui rend `iris` commode mais artificiellement simple, et ce qui rend `arbres_quebec` plus réaliste mais méthodologiquement exigeant.
