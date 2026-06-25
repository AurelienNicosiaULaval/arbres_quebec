# Stratégie de nettoyage et architecture du dépôt

## Pipeline en onze étapes

1. **Référencer les sources.** Le manifeste enregistre identifiant, URL, format, licence, rôle et emplacement attendu.
2. **Collecter sans écraser.** Le script de collecte écrit d'abord un fichier temporaire, calcule une empreinte SHA-256 et déplace atomiquement le résultat. Un fichier brut existant est conservé.
3. **Extraire sans altérer l'archive.** Le ZIP reste dans `data_raw/`; son contenu est extrait dans `data_intermediate/` avec un marqueur contenant l'empreinte de l'archive.
4. **Inspecter le GeoPackage.** Les tables sont découvertes via SQLite/GeoPackage. Le script échoue si une table ou une clé requise manque.
5. **Lire les tables utiles.** `DENDRO_ARBRES`, `DENDRO_ARBRES_ETUDES`, `PLACETTE`, `CLASSI_ECO_PE` et, pour PEP, `PLACETTE_MES`.
6. **Normaliser les noms.** `janitor::clean_names()` est appliqué sans modifier les fichiers sources.
7. **Décoder les codes.** Les feuilles `ESSENCES`, `ETAT`, `ETAGE`, `REG_ECO` et `DOM_BIO` du dictionnaire officiel sont jointes exactement.
8. **Harmoniser les mesures.** DHP mm→cm; hauteur dm→m; mesures observées et estimées conservées séparément; aucune imputation.
9. **Enrichir la taxonomie.** Une table de correspondance versionnée, revue et attribuée à VASCAN ajoute noms scientifiques, genres, familles et groupes fonctionnels.
10. **Créer les produits.** La version complète garde les anomalies signalées; la petite version applique une règle d'admissibilité et un échantillonnage équilibré documentés.
11. **Valider.** Le rapport Quarto vérifie clés, effectifs, distributions, valeurs manquantes, drapeaux, équilibre, exclusions et différence entre les deux versions.

## Rôle des dossiers

| Chemin | Rôle | Suivi Git recommandé |
|---|---|---|
| `data_raw/` | copies exactes des archives et documents sources | ignorer les fichiers volumineux; conserver `.gitkeep` et manifeste |
| `data_intermediate/` | GeoPackages extraits et tables temporaires régénérables | ignorer |
| `data_clean/` | CSV/Parquet finaux, dictionnaire et journaux d'exclusion | publier par version ou Git LFS selon taille |
| `R/` | fonctions réutilisables d'E/S, validation et dérivation | suivre |
| `scripts/` | scripts exécutables numérotés | suivre |
| `docs/` | diagnostic, schéma, activités et rapport Quarto | suivre |
| `references/` | manifeste, tables taxonomiques et décisions revues | suivre |
| `logs/` | journaux de collecte et de construction | ignorer les journaux locaux; archiver ceux d'une version publiée |
| `README.md` | décision, installation et commandes | suivre |
| `data_dictionary.csv` | contrat de données versionné | suivre |
| `LICENSE` | licence du code | suivre |
| `DATA_LICENSES.md` | licences et attributions des sources | suivre |
| `CITATION.cff` | citation du logiciel/dépôt | suivre |

## Décisions de nettoyage

- Une valeur impossible n'est pas corrigée par supposition; elle reçoit un drapeau.
- Les seuils très élevés servent au dépistage et non à l'exclusion automatique.
- Une date illisible devient `NA` avec journalisation; elle n'est pas remplacée par l'année du projet.
- Une taxonomie non appariée reste inconnue; le nom latin n'est pas construit à partir du nom français.
- La région administrative reste inconnue sans couche et jointure spatiales officielles.
- `ETAGE_ARB` est publié comme `canopy_stratum`, pas comme `crown_class`.
- Les codes d'essence agrégés restent dans la version complète et sont exclus de la cible pédagogique avec motif.
- La petite version utilise uniquement la hauteur observée, ce qui constitue une restriction de sous-échantillon publiée.
- Le DHP et la surface terrière ne doivent pas être utilisés simultanément comme variables indépendantes sans discuter leur relation déterministe.
