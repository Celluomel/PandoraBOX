# Méthode permanente — audit du harnais cognitif Lumina

Cette procédure est le cadre de travail durable pour l’audit du cerveau de Lumina. Elle reste applicable après une compaction de contexte, une nouvelle session Codex ou un redémarrage de Lumina. Le but est de corriger et de valider le fonctionnement du harnais cognitif complet, pas de compter des fichiers ou des ticks.

## Objectif et périmètre

Suivre des scénarios représentatifs depuis le message ou l’événement déclencheur jusqu’à la réponse visible et aux effets internes/aval. Pour chaque chemin, vérifier que les composants requis sont appelés dans le bon ordre, que leurs entrées et sorties sont reliées au même tour/cycle, que les décisions sont fondées sur leurs résultats réels, et que les effets annoncés ont effectivement été enregistrés.

Le périmètre principal comprend le tour conversationnel, le routage, l’assemblage du contexte, la mémoire et le profil, le fournisseur LLM, la validation de sortie, les événements post-réponse, l’affect, les croyances et objectifs, ainsi que la boucle interne et ses actions. Le Body n’est inclus que lorsqu’un scénario cognitif l’exige; il ne remplace pas l’audit du Brain.

## Règles de preuve

Classer chaque constat dans l’une de ces catégories et les garder distinctes :

1. **Présence** : le composant existe ou est initialisé.
2. **Exécution** : un reçu ou un journal identifie le composant, le tour/cycle et son statut.
3. **Sortie** : la valeur ou le résultat produit est lisible et respecte le contrat.
4. **Causalité** : une référence de sortie/entrée ou un identifiant parent prouve que l’étape aval a consommé le résultat amont.
5. **Effet** : l’état attendu a réellement changé ou persisté, vérifié par une lecture indépendante lorsque possible.
6. **Qualité** : le résultat répond au critère du scénario, comparé à un attendu explicite et à un témoin négatif.

Un tick, une sortie non vide, `success`, `pipeline_integrity=consistent` ou une réponse plausible ne prouve pas à lui seul la qualité ni l’effet. Un statut `unverified`, un échantillon manquant ou une inférence doit rester explicitement marqué comme tel. Relier les preuves avec `turn_id`, `cycle_id`, `parent_turn_id` et les références d’exécution; ne pas inférer la causalité seulement à partir de la proximité temporelle.

## Boucle de travail obligatoire

Pour chaque défaut découvert :

1. **Reprendre l’état** : lire `AGENTS.md`, ce document, le dernier point du rapport d’audit, `git status`, les derniers commits et l’état runtime disponible. Ne jamais supposer que Lumina est arrêtée ou démarrée.
2. **Définir le scénario et le critère** : préciser le déclencheur, les composants attendus, le résultat correct, les effets attendus, les témoins négatifs et les conditions d’abstention/erreur.
3. **Tracer le chemin réel** : inspecter le code et les reçus/logs portant le même identifiant. Localiser la première divergence entre l’entrée, la décision, la sortie et l’effet aval.
4. **Établir la cause** : reproduire le défaut ou l’expliquer à partir d’une preuve; distinguer défaut de code, configuration, fournisseur indisponible, données absentes et défaut d’instrumentation.
5. **Corriger le mécanisme causal** : conserver les fonctions cognitives requises; ne pas masquer un défaut par une liste de mots, une réponse pré-écrite, un faux succès ou un nouveau veto générique. Les filtres lexicaux ne doivent pas remplacer le routage sémantique ni le raisonnement.
6. **Valider localement** : tests ciblés sur le cas fautif, les cas voisins et le témoin négatif; tests plus larges du chemin affecté; compilation et vérification diff. Rapporter exactement ce qui a été exécuté et ses limites.
7. **Regrouper les chargements live** : ne redémarrer Lumina qu’après un lot cohérent de changements qui nécessite le rechargement, sauf si le diagnostic runtime l’exige. Avant toute action, inventorier le PID propriétaire, les parents, la commande, les ports et le profil d’audit. Utiliser `scripts/restart_lumina_audit.ps1`; ne jamais démarrer une seconde instance à l’aveugle ni arrêter un PID non identifié. Après redémarrage, vérifier identité du PID, `/status` prêt, `/next/` HTTP 200, reçus du nouveau processus et résultat du scénario.
8. **Vérifier les effets aval** : confirmer que les étapes suivantes ont consommé la sortie par référence, puis relire l’état réellement modifié (historique, profil, mémoire, objectif, croyance, tâche ou résultat de livraison). Vérifier aussi l’absence des effets interdits.
9. **Mettre à jour le rapport et Git** : consigner cause, changement, preuves locale/live, limites, scénario fermé et prochain travail. N’augmenter la progression que lorsqu’un critère complet de piste est rempli. Committer uniquement les fichiers de l’audit explicitement sélectionnés; ne pas inclure d’artefacts non suivis ou de travail étranger. Pousser quand l’accès Git est disponible et confirmer le SHA distant.
10. **Continuer** : reprendre le prochain défaut de cause racine dans le plan global. Ne pas conclure, s’arrêter ou demander un redémarrage simplement parce qu’un petit correctif est terminé. Demander une action utilisateur uniquement si une interaction réelle est indispensable (par exemple une question de test à poser à Lumina), et continuer entre-temps le travail indépendant.

## Couverture représentative minimale

Maintenir une matrice scénario → modules requis → preuves de sortie → causalité → effets → qualité. Inclure au minimum :

- question factuelle simple et réponse sociale, pour mesurer le chemin direct et les appels superflus;
- suivi multi-tour dépendant de l’historique;
- rappel mémoire et profil utilisateur, avec source admissible, admission/refus, persistance et réinjection vérifiées;
- recherche externe activée et désactivée, avec décision de routage, sources réellement utilisées et poids du résultat dans la réponse;
- question d’action/objectif, avec faisabilité, plan, exécution et résultat distingués;
- introspection/affect et conflit/correction, en reliant les signaux internes au contenu sans prétendre à des états non enregistrés;
- boucle interne, de la proposition sélectionnée à l’action, au reçu, à l’effet mesuré et à la révision de l’objectif;
- panne fournisseur, extraction différée ou échec aval, pour vérifier reprise, isolation et absence de faux succès.

Adapter la couverture au code actuel; ne pas déclarer un module « inutilisé » parce qu’il n’a pas de tick dans un seul scénario. Le classer selon son rôle : requis pour un scénario donné, conditionnel, facultatif/conseil, critique de sécurité, indisponible, ou non attribuable par instrumentation.

## Gestion des pistes et progression

Garder une liste stable de pistes globales avec, pour chacune : hypothèse de défaut, scénarios requis, critère de fermeture, preuves acquises, preuves manquantes, statut du correctif, statut live et lien Git. Une piste est fermée seulement lorsque son critère complet est satisfait; les tests locaux seuls ne valident pas un changement live, et un test live unique ne valide pas une qualité générale.

Le pourcentage global est `pistes entièrement fermées / pistes définies`, avec la liste et les critères visibles dans le rapport. Ne pas recalculer le dénominateur pour gonfler artificiellement le progrès. Si le plan change, documenter la raison et la version avant de recalculer.

## Communication à chaque reprise

Donner une mise à jour seulement sur un changement matériel : piste en cours, cause démontrée ou réfutée, code/tests modifiés, validation locale/live et prochaine étape concrète. Toute réponse d’état doit distinguer les faits établis des hypothèses. Ne jamais annoncer « fixé » quand la correction n’est que locale ou non chargée; ne jamais perdre le but global au profit du dernier log observé.
