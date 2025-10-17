# TODO - Améliorations de l'interface utilisateur

## Améliorations à implémenter

### Corrections (fix)
- [x] **Fermeture de projet** : Empêcher l'expansion automatique d'un projet lors de sa mise à jour s'il a été fermé manuellement par l'utilisateur
- [x] **Hipster pipe** : Ne pas afficher l'animation de succès pour une pipeline qui n'est pas actuellement sélectionnée
- [ ] **Innactivité** : Après une longue période d'inactivité il n'y a plus de chargemetn des pipeline automatique

### Nouvelles fonctionnalités (feat)
- [x] **Timestamp pipeline** : Afficher le timestamp de création/exécution des pipelines + info tool sur job : date de mise à jour du job + date de création du job
- [ ] **Delete pipeline** : Retirer une pipeline de l'affichage avec un petit icone poubelle à droite de la ligne
- [ ] **Environnement cible** : Afficher l'environnement cible (target) des pipelines
- [ ] **Bouton Clear** : Ajouter un bouton pour effacer l'affichage d'une pipeline
- [ ] **Bouton Retry** : Implémenter un bouton pour relancer une pipeline
- [ ] **Menu contextuel** : Ajouter un menu contextuel (clic droit) avec des actions rapides
- [ ] **Informations du projet** : Afficher les détails du projet lorsqu'il est sélectionné

### Améliorations d'interface (ui)
- [ ] **Alternance de couleurs** : Utiliser des nuances de couleurs alternées pour les pipelines d'un même projet pour une meilleure différenciation visuelle

## Notes
- Priorité : Les éléments sont listés par ordre de priorité suggéré
- Format : Suivre le format [conventionnal commits](https://www.conventionalcommits.org/) pour les messages de commit (fix:, feat:, ui:)
