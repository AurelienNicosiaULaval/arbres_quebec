# Étapes qui exigent une intervention humaine

1. **Confirmer les conditions d'utilisation et l'attribution** à la date de collecte. Conserver une copie des métadonnées ou leur empreinte.
2. **Télécharger l'archive PET5** si le gros téléchargement automatique est désactivé, puis la déposer dans `data_raw/PET5/` sans la renommer après création du manifeste.
3. **Vérifier l'intégrité** : taille non nulle, ouverture ZIP, présence d'un GeoPackage et somme SHA-256 consignée.
4. **Inspecter les versions de protocole** lorsque plusieurs années ou versions sont combinées. Toute rupture doit être documentée.
5. **Réviser la table taxonomique** `references/species_taxonomy_crosswalk.csv`. Aucun appariement flou n'est accepté automatiquement.
6. **Décider du traitement des codes agrégés d'essence**. Ils restent dans la version complète; leur exclusion de la cible pédagogique doit être approuvée et consignée.
7. **Examiner les seuils de valeurs suspectes** dans `R/helpers_validation.R`. Ils servent à signaler, non à supprimer; ils doivent être adaptés si une norme officielle plus précise est retenue.
8. **Vérifier les quatre espèces sélectionnées** après exécution. Le script les choisit par fréquence admissible et non à partir d'une liste présumée.
9. **Contrôler la représentativité géographique et temporelle** de la petite version. Un équilibre d'espèces n'implique pas un équilibre de régions ou d'années.
10. **Relire le journal d'exclusion** avant publication et expliquer les restrictions en cas complets de la petite version.
11. **Rendre le rapport Quarto** et résoudre tout contrôle bloquant : clés dupliquées, unités incohérentes, jointures plusieurs-à-plusieurs imprévues ou absence de fichiers.
12. **Remplacer les métadonnées de citation** dans `CITATION.cff`, notamment le dépôt et les auteurs.
