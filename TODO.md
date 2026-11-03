# TODO - Améliorations de l'interface utilisateur

## Améliorations à implémenter

### Corrections (fix)
- [x] **Fermeture de projet** : Empêcher l'expansion automatique d'un projet lors de sa mise à jour s'il a été fermé manuellement par l'utilisateur
- [] **Hipster pipe** : Ne pas afficher l'animation de succès pour une pipeline qui n'est pas actuellement sélectionnée
- [ ] **Innactivité** : Après une longue période d'inactivité il n'y a plus de chargemetn des pipeline automatique
- [x] **Erreur HTTP code filter** : Filtrer des codes https en erreur
- [ ] ** Ligne pipeline empty ** : si le message des pipeline vide est affiché et qu'une pmipelin arrive, il faut retirer cette phrase.
- [ ] ** Header logs pas a jour ** : le header ne se met pas a jour au fur et a mesure du changemetn de stage
### Nouvelles fonctionnalités (feat)
- [x] **Timestamp pipeline** : Afficher le timestamp de création/exécution des pipelines + info tool sur job : date de mise à jour du job + date de création du job
- [x] **Delete pipeline** : Retirer une pipeline de l'affichage avec un petit icone poubelle à droite de la ligne
- [x] **Environnement cible** : Afficher l'environnement cible (target) des pipelines juste avant le timestamp
- [x] **Bouton Retry** : Implémenter un bouton pour relancer une pipeline
- [ ] ** Detection token expiré ** : la detection du token expiré ne fonctionne pas correctement
- [ ] **Menu contextuel** : Ajouter un menu contextuel (clic droit) avec des actions rapides
- [ ] **Informations du projet** : Afficher les détails du projet lorsqu'il est sélectionné
- [ ] **Informations de la pipeline** : Afficher les détails de la pipeline lorsqu'elle est sélectionnée
- [ ] **Informations du job** : Afficher les détails du job lorsqu'il est sélectionné
- [ ] **Informations de l'historique** : dans la selection "projet" afficher les denieres piepline.
- [ ] **Informations job failer car syntax erreur yaml** :
- [ ] **GitHub workflows** : Adapter l'application pour gérer aussi les workflows GitHub Actions

### Améliorations d'interface (ui)
- [ ] **Alternance de couleurs** : Utiliser des nuances de couleurs alternées pour les pipelines d'un même projet pour une meilleure différenciation visuelle

## Notes
- Priorité : Les éléments sont listés par ordre de priorité suggéré
- Format : Suivre le format [conventionnal commits](https://www.conventionalcommits.org/) pour les messages de commit (fix:, feat:, ui:)
