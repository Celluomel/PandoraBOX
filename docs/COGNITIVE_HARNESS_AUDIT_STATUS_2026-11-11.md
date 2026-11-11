# Audit du harnais cognitif — état et prochaines étapes

**Date :** 11 novembre 2026
**Statut :** audit en cours — conclusion globale non établie.

## Objectif de l’audit

Établir, pour des scénarios représentatifs du Brain, que les composants requis sont réellement exécutés, que leurs sorties sont cohérentes et de qualité suffisante, et que leurs effets en aval peuvent être reliés au tour qui les a déclenchés. Un tick, un statut `healthy` ou une réponse livrée ne démontre pas à lui seul que le raisonnement est correct.

Le périmètre de ce document est le **cerveau et son harnais cognitif** : chemin d’un tour, contexte et mémoire, objectifs, planification, génération, validation, effets en aval et observabilité. Ce n’est pas un audit du matériel Body.

## État exécutif

- Lumina a répondu à un scénario de vérification de son manifeste live. L’API locale a indiqué un processus prêt et un modèle LM Studio chargé.
- Le manifeste a évolué après le démarrage : à environ 44 secondes, il indiquait 0/43 ticks; à environ 238 secondes, il indiquait 32/43 modules observés, 68 ticks et 0 erreur instrumentée. Le premier relevé était un instantané de démarrage, pas un résultat stable.
- Les compteurs donnent une preuve d’activité instrumentée, **pas** une preuve d’exécution de chaque fichier Python, de qualité sémantique, ni de causalité entre les modules.
- Le test conversationnel à deux tours a mis au jour une vraie lacune : la réponse précédente n’était pas correctement reliée au tour de suivi dans la trace. La frontière d’historique a été corrigée dans `17ae81c`; le chaînage des candidats et preuves dans la trace a ensuite été ajouté dans `045e82a`. Le processus courant avait chargé ces changements après le redémarrage de l’utilisateur.
- Des tests locaux ciblés passent. Ils ne remplacent pas la validation live après redémarrage ni les scénarios cognitifs restants.

## Preuves recueillies

| Domaine | Fait observé | Ce que cela prouve | Limite actuelle |
|---|---|---|---|
| Disponibilité Brain | Les endpoints locaux de statut et d’interface ont répondu; `ready=true`, Persona et Orchestrator disponibles, modèle `lmstudio/gemma-4-e4b-uncensored-hauhaucs-aggressive`. | Le processus interrogé était vivant et capable de recevoir un tour. | Ne prouve ni la qualité de chaque réponse ni le bon fonctionnement de tous les modules. |
| Registre de modules | 43 entrées au manifeste. Relevé initial vers 44 s : 0 tick observé. Relevé vers 238 s : 32 modules avec tick, 68 ticks, 0 erreur instrumentée; 11 initialisés sans tick observé dans ce relevé. | Une partie substantielle du harnais a produit des ticks instrumentés après échauffement. | `sans tick observé` ne signifie pas forcément « code jamais exécuté ». Le statut dépend de la fenêtre et du scénario. Un compteur d’erreurs à zéro ne valide pas les sorties. |
| Tour d’introspection | Le Brain a rapporté les compteurs du manifeste avec la réserve qu’ils ne valident pas la qualité cognitive. | La réponse correspondait aux valeurs observées au moment du premier relevé. | L’instantané était précoce; les valeurs ont changé avec le temps. Il faut dater et associer l’instantané au tour. |
| Continuité entre deux tours | Le suivi rappelait le résultat précédent, mais la trace ne l’associait pas correctement au tour antérieur. | Le comportement a exposé un défaut reproductible de frontière de tour / liaison de preuve. | La correction n’a pas encore été vérifiée sur le processus redémarré. |
| Traçage et qualité | Les réponses de registre distinguaient les compteurs d’exécution de la justesse cognitive. | Une première capacité à exprimer les limites des métriques a été observée. | Les effets aval et les sorties de modules individuels ne sont pas encore vérifiés scénario par scénario. |

## Défaut de liaison de continuité et correction

Le mécanisme ajoutant la preuve de la réponse précédente cherchait à retirer l’échange courant de l’historique en comparant le texte utilisateur exact. Dans le chemin testé, `LLMManager.history` contenait un prompt enrichi/décoré; l’égalité échouait et le code traitait à tort la réponse courante comme une réponse antérieure. Cela pouvait produire une liaison de trace erronée malgré le contenu conversationnel rappelé.

La correction utilise maintenant un indicateur explicite `current_exchange_recorded` et retire l’échange courant selon son rôle, plutôt qu’en comparant le texte. Le correctif est dans `17ae81c` (`Link prior answer using turn boundary`), après `dbaa454` qui avait introduit la récupération de la preuve précédente.

**État de validation :** correction testée en live après redémarrage utilisateur; le tour `ad1c22f7-5086-45d1-a469-91236f7f4b8f` a relié le rappel au tour `8865020b-14ba-4f7e-ae32-9d7e9eaa192b`. Le correctif de trace associé a été commité ensuite dans `045e82a`.

## Vérifications locales déjà exécutées

- `tests/test_turn_execution_evidence.py` et `tests/test_self_description_prompt.py` : **17 passed**, 9 avertissements de dépréciation/paquet.
- `py_compile` de `cognition/persona_bridge.py` et `cognition/self_description.py` : réussi.
- `git diff --check` : réussi.
- Commit `17ae81c` présent sur `main` et `origin/main` au dernier relevé.

Ces résultats couvrent le correctif de liaison et des tests de prompt associés; ils ne constituent pas l’exécution de toutes les suites du dépôt ni un audit complet du harnais.

## Ce qui reste inconnu ou insuffisamment prouvé

1. **Liaison live après redémarrage :** la trace du second tour doit référencer l’identifiant/fingerprint de la réponse précédente, sans l’identifier à tort comme la réponse courante.
2. **Couverture module par module :** les 43 modules doivent être classés par rôle et scénario. Pour chacun, il faut distinguer initialisé, tick observé, sortie présente, sortie vide, effet latéral, erreur et indisponible. Un tick seul n’est pas un résultat.
3. **Cohérence des sorties :** les valeurs produites doivent être comparées aux entrées du tour et aux invariants du module; les contradictions et valeurs de repli doivent être visibles.
4. **Causalité en aval :** mutations d’objectifs, mémoire, workspace, apprentissage proactif et réponses doivent être rattachés à un `turn_id` et, lorsque disponible, à une preuve d’écriture/lecture ou à un résultat d’action.
5. **Mesures d’évaluation :** un ancien instantané de `/state` affichait 0 essai et 0 confirmation pour l’audit cognitif, ainsi que des taux de résolution/confirmation indisponibles. Cet instantané n’est pas postérieur au dernier redémarrage et doit être relu avant d’en tirer une conclusion actuelle.
6. **Suites complètes :** seules les suites ciblées ci-dessus sont comptées comme réussies pour le correctif récent. Les autres tests du dépôt ne sont pas déclarés passés par ce document.

## Plan d’exécution

### 1. Confirmer le correctif en live — à faire lors du redémarrage final

Ne pas redémarrer pendant la phase de corrections/audit. Après les corrections cumulées, redémarrer Lumina une seule fois et vérifier :

1. Attendre que le processus soit prêt et que le manifeste ait eu le temps de se stabiliser; conserver l’uptime et l’heure du relevé.
2. Envoyer un premier tour demandant le nombre de modules avec tick observé et les limites de cette mesure.
3. Envoyer un suivi explicite demandant de rappeler le résultat précédent et sa limite.
4. Inspecter les traces des deux tours : `turn_id`, identifiant/fingerprint de sortie, preuve de récupération précédente et association de la réponse finale. Vérifier que les fingerprints précédent et courant ne sont pas confondus.
5. Comparer le texte de la réponse à l’instantané de manifeste attaché au premier tour. Verdict réussite uniquement si le rappel et le lien de trace sont corrects; sinon conserver le cas comme échec et remonter à la cause.

### 2. Construire la matrice d’exécution par scénario

Pour chaque scénario, enregistrer les modules requis, leurs ticks dans le tour, leurs sorties, leur fraîcheur/qualité, le consommateur en aval et la preuve d’effet. Inclure au minimum :

- conversation ordinaire et finalisation de réponse;
- rappel de contexte et continuité multi-tour;
- introspection sur l’état et l’architecture du Brain;
- extraction sémantique et création/révision d’objectifs;
- planification d’un objectif, résultat `completed`/`failure`/`none` et vérification qu’aucune action n’est revendiquée sans preuve;
- mémoire et workspace : écriture, récupération ultérieure et provenance;
- traitement d’une réponse déterministe et traitement d’une réponse générée, avec contrats de preuve distincts.

Pour chaque case, rapporter **observé**, **inféré** ou **inconnu**. Ne pas interpréter `side_effect_only` comme une sortie sémantiquement validée.

### 3. Examiner les défauts structurels, puis corriger leurs causes

- Tracer pourquoi certains modules ne tickent pas dans les scénarios où ils sont attendus : déclencheur absent, tâche périodique, voie conditionnelle, instrumentation manquante ou défaut réel.
- Relier les objectifs et changements de workspace au tour source, puis vérifier leur effet sur le tour suivant.
- Déterminer pourquoi les compteurs d’essais/confirmations cognitifs sont à zéro ou indisponibles dans l’ancien instantané; corriger le contrat d’instrumentation si les expériences existent mais ne sont pas comptabilisées.
- Vérifier la cohérence des sorties amont/aval avec des invariants et les entrées du même tour, pas en ajoutant un filtre lexical sans diagnostic causal.

### 4. Vérifier les changements et conclure

- Lancer les tests ciblés liés à chaque correction, puis les suites pertinentes plus larges; distinguer explicitement passé, échoué, bloqué et non exécuté.
- Rejouer live après chaque changement nécessitant un redémarrage.
- Mettre à jour ce rapport avec les identifiants de tours et preuves observables.
- Ne déclarer l’audit conclu que lorsque les scénarios représentatifs ont des sorties et effets aval vérifiés, et que les modules sans preuve sont classés et expliqués.

## État Git et préservation du worktree

À l’état actuel de cette reprise, `main` contient les commits d’audit jusqu’à `d0ff7a0`, tandis que `origin/main` reste sur `17ae81c` (avance locale, pas encore poussée). Le worktree contient des modifications et fichiers non suivis préexistants sans rapport avec l’audit, notamment des changements Body, pages, tests et artefacts. Ils restent intacts et exclus des commits d’audit.

## Critère de clôture

L’audit ne sera terminé que lorsque chaque scénario retenu reliera une entrée identifiée à des modules effectivement requis/exécutés, à des sorties cohérentes, et à des effets aval vérifiables; lorsque les modules sans preuve seront expliqués par leur rôle ou corrigés; et lorsque les tests locaux et vérifications live seront rapportés sans assimiler activité instrumentée et qualité cognitive.

## Reprise live sans redémarrage — 11 novembre 2026

### Santé et manifeste

- Lecture live de `/status` et `/api/interface/status` : Brain prêt, LM Studio disponible, Orchestrator actif; l’uptime observé était d’environ 228 s au premier relevé.
- Avant interaction : 43 modules enregistrés; 11 modules avec tick observé, 23 ticks, 0 erreur instrumentée. Après l’échauffement du tour : le manifeste injecté dans la trace comptait 34 modules avec tick, 64 ticks, 0 erreur, 9 initialisés sans tick et 0 indisponible. Au tour suivant, il comptait 36 modules, 110 ticks, 0 erreur. Les valeurs varient avec les cycles autonomes et le moment de capture; elles ne doivent pas être traitées comme compteurs causés par le message.
- Le contexte Body était `no_current_evidence`, la caméra Brain inactive. Ces champs servent à distinguer l’absence de données de l’échec d’exécution.

### Vérification live multi-tour

Trois tours ont été envoyés au processus courant, sans redémarrage :

1. `aef76346-c48d-4a45-827e-3f6840bc6693` : question factuelle sur les compteurs du manifeste et leur limite. Réponse livrée; la trace indique les entrées, prompt, génération, sécurité et finalisation. `architecture_claim_validation=replaced_unverified_claims`. La sortie finale a un fingerprint; les stages de validation n’enregistraient alors pas le candidat ni la sortie corrigée comme relation amont/aval.
2. `8865020b-14ba-4f7e-ae32-9d7e9eaa192b` : suivi demandant de rappeler le résultat précédent. Réponse livrée, mais le texte affirmait que le lien était direct sans preuve explicite dans les stages du tour. Le libellé ne contenait pas les marqueurs « modules/ticks » attendus par le chemin déterministe; ce tour n’est donc pas un test valide du garde-fou de rappel.
3. `ad1c22f7-5086-45d1-a469-91236f7f4b8f` : suivi reformulé avec « modules » et « ticks ». Lumina a rendu une réponse déterministe qui cite le contenu du tour précédent et dit explicitement qu’il est lié au tour `8865020b-14ba-4f7e-ae32-9d7e9eaa192b`. La même réponse rapporte pour la trace courante 36 modules, 110 ticks et 0 erreur instrumentée. **Le chemin de récupération et de liaison est validé en live sur le code chargé.** Cela confirme la correction `17ae81c` déjà chargée par le redémarrage utilisateur.

La preuve reste circonscrite à ce scénario et à ce processus. Elle ne valide pas les rappels libres sans marqueurs, la qualité de tous les outputs, ni les effets cognitifs généraux.

### Défaut de traçabilité trouvé et correctif commité

La trace live du premier tour montrait que le garde-fou pouvait remplacer le texte généré, mais `architecture_claim_validation` ne conservait que son statut. Le fingerprint final apparaissait plus tard dans `response_finalization`; aucun chaînage explicite ne reliait le candidat généré, la preuve de tour antérieur, la sortie corrigée et le contrôle de sécurité.

Correction committée dans `045e82a` :

- enregistrer uniquement des métadonnées minimales de la preuve antérieure (`turn_id`, fingerprint, booléen de liaison), sans texte privé;
- fingerprint-er le candidat de génération puis la sortie du garde-fou, et déclarer les stages qu’ils consomment;
- faire consommer à `output_safety` le stage de validation pour que la trace suive bien la sortie effectivement présentée.

Fichiers concernés : `cognition/persona_bridge.py`, `tests/test_turn_execution_evidence.py` et ce rapport. Le code est commité, mais son effet live reste à vérifier après le redémarrage final.

### Vérifications de cette reprise

- `tests/test_turn_execution_evidence.py` + `tests/test_self_description_prompt.py` : **19 passed**, 9 avertissements.
- `tests/test_brain_workflow_status.py` : **9 passed**, 3 sous-tests passés, 9 avertissements.
- `py_compile` des fichiers du correctif et `git diff --check` ciblé : réussis.
- `tests/test_lumina_network_peer_turns.py` : le test peer qui bloquait en sandbox se figeait avant l’entrée dans le test, dans `asyncio` Windows `socketpair`/`accept`. Le test isolé puis la suite complète ont passé hors sandbox : **32 passed**, 3 sous-tests passés. La cause était la restriction d’accès au socket local du sandbox, pas un défaut du harnais.

### Travail restant avant le redémarrage final

1. Continuer l’audit des effets aval en testant séparément les modules requis pour continuité, mémoire, objectifs et planification.
2. Pour chaque scénario, consigner le tour, les étapes requises, les sorties/fingerprints, les mutations et leur preuve de récupération; signaler ce qui reste inconnu au lieu d’inférer la qualité depuis les ticks.
3. Quand les corrections logicielles sont terminées, demander un seul redémarrage final et vérifier les changements cumulés en live; ensuite seulement conclure l’audit.

## Suivi naturel d’audit — correctif local du 11 novembre

Le deuxième tour live (`8865020b-14ba-4f7e-ae32-9d7e9eaa192b`) a révélé un défaut distinct : une formulation naturelle (« dans le test d’audit que je viens de te demander, rappelle les compteurs… ») n’activait pas le chemin de preuve. La réponse libre affirmait pourtant être liée au tour précédent. Le suivi reformulé avec « modules » et « ticks » activait le chemin déterministe et établissait correctement le lien. La cause était donc le routage trop étroit, pas l’absence de la preuve conservée.

Le routage reconnaît maintenant une référence à un tour antérieur lorsqu’elle porte sur un audit/une trace et des compteurs ou leur exécution. Le garde-fou réutilise alors les preuves conservées, signale un lien absent au lieu de l’inventer, puis distingue le snapshot courant des limites sémantiques. Cela traite le routage de cette famille de demandes; cela ne remplace pas une résolution sémantique générale du dialogue.

- Tests `tests/test_self_description_prompt.py`, `tests/test_turn_execution_evidence.py` et `tests/test_brain_workflow_status.py` : **29 passed**, 3 sous-tests passés, 9 warnings.
- Tests `tests/test_module_tick_log.py` et `tests/test_goal_engine_execution_order.py` : **11 passed**, 9 warnings. Ces tests valident les contrats de journalisation et l’ordre d’exécution du moteur d’objectifs, pas encore les effets d’un tour live.
- Le processus live est resté prêt pendant cette correction (`/status`: `ready=true`, modèle Gemma chargé, uptime ~1154 s). Aucun redémarrage n’a été effectué; le correctif local n’est donc pas encore chargé par ce processus.
- Le test rejoue la formulation qui avait échoué et vérifie que le rappel cite le `turn_id` fourni, donne les compteurs présents dans la trace courante et énonce les limites.
- Correctif commité dans `92ef6db`; tout autre changement préexistant du worktree reste hors de portée.

## Cycle d’auto-audit / essais — défaut et correction locale

La lecture live de `/api/interface/cognitive-health` a donné `total_audits=50`, `total_trials=0`, `active_trial=null`, `mean_skill_depth=0.3` pour une cible de `1.0`, et `consecutive_under.mean_skill_depth=180`. Les taux de confirmation d’expériences et de résolution de questions étaient indisponibles. Le fichier persistant `data/persona/cognitive_params.json` confirme les 50 snapshots, zéro essai et aucune tentative de proposition conservée.

Le code explique le trou d’observabilité : après deux mesures sous cible, le moteur appelle le LLM via `sync_slot(priority=3, skip_if_busy=True)` sans attente. Une indisponibilité, une réponse vide ou un JSON invalide produit `None`; aucun état persistant ne distingue ces cas. Les compteurs ne permettent donc pas de savoir si la cause historique était la saturation du LLM, une réponse invalide ou une autre panne. **La saturation est une hypothèse plausible, pas un fait observé.** Les signaux avec dénominateur nul sont correctement `null` et ne doivent pas être traités comme 0 %.

Correction locale en cours de validation :

- attendre au plus 5 s pour obtenir le créneau LLM de priorité 3, sans attente infinie;
- conserver les tentatives séparément des essais réellement activés, avec cycle, dimension, statut et détail borné; afficher le total et la dernière cause dans `status_summary`;
- différencier créneau occupé, erreur LLM, réponse vide/invalide, paramètre refusé, aucun changement et essai activé. Les changements de paramètres restent bornés et aucun essai n’est déclaré avant activation effective.

Vérification locale : **50 passed**, 3 sous-tests passés, 9 warnings sur le lot des tests de données santé, workflow de Brain, traçage de tour, manifeste de ticks et exécution GoalEngine. Cette modification ne peut être confirmée live qu’après le redémarrage final. Avant le correctif, l’API de santé n’exposait pas les tentatives; les valeurs historiques n’identifient donc pas la cause exacte.

## Taille et ordre du statut du planner — correctif local

Le endpoint de santé a renvoyé **1 194 plans** alors que le panneau du dashboard n’en affiche que trois. Dans l’ordre courant, les premières lignes comprenaient des plans terminés avec « next=done » avant les plans actifs. L’historique est utile au planner, mais le renvoyer en entier à chaque poll est inutile et rend le panneau trompeur.

Le contrat `LongHorizonPlanner.status()` renvoie maintenant les plans actifs en premier, puis les plans archivés récents, avec une limite de 20 résumés. Chaque ligne expose aussi son état (`active`, `completed`, etc.). Il conserve la taille totale (`total_plans`) et le nombre renvoyé; le stockage persistant n’est pas purgé. Un test couvre le tri, la limite et le comptage.

La suite incluant `tests/test_intention_planning.py` et les lots de workflow, audit, ticks et traçage passe : **75 passed**, 3 sous-tests, 8 warnings. Le process live continuera à exposer l’ancien résultat jusqu’au redémarrage final.

## Avancement falsifié et redispatch asynchrone — correction locale

L’examen du chemin `InternalLoop → GoalActionExecutor → LongHorizonPlanner` a révélé deux défauts d’exécution qui pouvaient fausser la preuve d’efficacité du harnais :

- `record_autonomous_action_outcome()` appelait `record_step_outcome()` même après un échec. Cette dernière fonction incrémentait toujours `steps_completed` et marquait l’étape `completed`. Le même plan pouvait donc rapporter un dernier résultat `failure` tout en affichant une progression avancée.
- Les actions asynchrones (`self_question`, `web_search`, `bisociative`) n’avaient pas de marqueur d’exécution en cours. Un cycle suivant pouvait lancer une seconde coroutine pour le même objectif et la même action avant que la première ne termine; les prédictions en attente, indexées par cette paire, pouvaient alors être remplacées.

Corrections locales : les résultats négatifs gardent l’étape en attente, enregistrent tentative et détail, sans incrémenter la progression; une action réussie seule avance l’étape. L’exécuteur protège chaque paire objectif/action asynchrone par un verrou et libère ce verrou à la fin, y compris lors d’une exception. Les erreurs qui échappent à la coroutine sont finalisées comme échec au lieu de laisser une prédiction orpheline.

Vérification : `tests/test_intention_planning.py`, `tests/test_goal_engine_execution_order.py` et `tests/test_brain_workflow_status.py` : **38 passed**, 3 sous-tests passés, 8 avertissements. `git diff --check` ciblé passe. Le process Lumina n’a pas été redémarré; ces changements ne sont donc pas encore chargés live.

La provenance reste incomplète : les actions autonomes n’ont pas encore un identifiant d’exécution commun propagé de l’InternalLoop jusqu’au résultat du planner et au ledger causal. Les résultats peuvent être reliés à l’objectif et au type d’action, mais pas encore à un cycle/tour précis par une clé stable. C’est le prochain point à auditer avant de conclure.

## Attribution des résultats entre plans — correction locale complémentaire

L’audit du flux a montré que `GoalActionExecutor` transmettait aussi son action au plan d’aspiration ayant la plus haute tension dès que son nom d’opération correspondait. Une action attachée à un objectif pouvait donc faire avancer un plan d’aspiration sans lien avec cet objectif. De plus, le planner pouvait marquer une étape `user_question` terminée après un simple tick autonome ou après n’importe quel tour de chat : aucun identifiant de question ne reliait le tour à la question effectivement posée.

Corrections : l’exécuteur ne transmet désormais les résultats qu’au plan de l’objectif réellement exécuté; la mise à jour directe d’un plan d’aspiration exige un domaine explicitement identifié. Le tick autonome ignore les étapes `user_question`, et le cycle de chat ne les complète plus sans reçu/corrélation de réponse. C’est une perte volontaire de faux progrès : la vraie liaison question→réponse reste à implémenter avant de pouvoir valider ces étapes comme terminées.

Une régression a d’abord échoué en révélant que le tick autonome marquait toujours `user_question` terminé; le filtre a été corrigé et rejoué. Résultat final du lot `tests/test_intention_planning.py`, `tests/test_goal_engine_execution_order.py`, `tests/test_brain_workflow_status.py`, `tests/test_module_tick_log.py`, `tests/test_turn_execution_evidence.py` : **56 passed**, 3 sous-tests passés, 8 avertissements. Ce lot inclut aussi les tests de progression après échec, provenance explicite et absence de redispatch asynchrone. Ces changements restent locaux jusqu’au redémarrage final.

## Sémantique du registre de ticks — correction locale

Le registre de modules classait `healthy` toute méthode qui se terminait sans exception, y compris une méthode dont le résultat était `None` sans contrat `-> None`, ou un objet opaque dont le contenu n’était pas inspecté. Cela confondait réussite d’exécution et preuve d’une sortie exploitable.

Le registre distingue maintenant `output_unverified` pour une sortie vide, opaque ou de forme inconnue; `side_effect_only` reste interprété comme une exécution déclarée à effet de bord; un résultat numérique non fini reste `degraded`; `healthy` indique seulement une sortie présente et des contrôles structurels/numeric de base réussis, sans prétendre valider le sens cognitif. Le snapshot de l’InternalLoop applique le même contrat que le registre.

Le lot ciblé (ticks, workflow, intention/planification, traçage de tour) passe : **57 passed**, 3 sous-tests passés, 9 avertissements. `py_compile` des modules modifiés et `git diff --check` passent. Le changement n’est pas chargé dans Lumina avant le redémarrage final.

## Étapes sociales du planner — récupération sans faux effet mesuré

Après avoir empêché la progression d’un plan d’aspiration à partir d’un tour utilisateur non corrélé, une étape de récupération persistée `user_question` aurait pu rester bloquée. Le code de création nommait en réalité cette étape comme une question utilisateur, alors que `_execute_autonomous_social_step()` ne faisait qu’émettre un probe interne. La correction distingue maintenant `social_probe` d’une vraie question; les anciennes étapes de récupération sont migrées au chargement et réécrites sans supprimer l’historique du plan.

Les étapes terminées par ce probe sont enregistrées comme exécutées, mais ne reçoivent plus des valeurs numériques fixes de coût/gain. La déviation n’est calculée que si coût **et** effet sont effectivement mesurés; sinon le journal mentionne `effect_not_measured=true`. Le probe interne peut donc compléter son opération, sans prétendre avoir mesuré un gain de confiance utilisateur.

Résultat du lot ciblé : **60 passed**, 3 sous-tests passés, 8 avertissements. Il inclut la migration d’un ancien plan, le maintien d’une vraie étape `user_question` sans réponse, l’exécution du `social_probe` et l’absence de déviation numérique fabriquée. `py_compile` et `git diff --check` réussis. Le process live reste volontairement sur son code antérieur, sans redémarrage.

## Lecture de télémétrie sans mutation et preuve du premier tick paresseux

Deux défauts supplémentaires ont été isolés pendant la poursuite de l’audit :

- `LongHorizonPlanner.status()` et `factual_self_report_snapshot()` appelaient la synchronisation qui ferme les plans dont le but source est terminé. Une requête de statut ou d’auto-description pouvait donc muter et persister le plan; la lecture n’était pas pure. La fermeture relève du cycle de synchronisation du planner. Les fonctions de lecture ne font désormais que rapporter l’état mémorisé. Le test vérifie que le plan reste inchangé durant la lecture, et que le cycle explicite de synchronisation le ferme.
- Les modules cognitifs créés paresseusement étaient sondés à la fin du cycle lent. Si le constructeur et le premier `tick()` étaient dans le même cycle, cet appel échappait au registre. `InternalThoughtLoop.__setattr__` attache désormais le probe au module au moment de son affectation, avant son premier appel; le rafraîchissement ciblé évite de rescanner les 43 modules à chaque affectation. Le test reproduit une affectation tardive puis vérifie la capture du premier tick et de sa sortie.

Vérification locale : `tests/test_intention_planning.py` + `tests/test_module_tick_log.py` **45 passed**, 7 avertissements Pydantic préexistants; `py_compile` et `git diff --check` réussis. Les changements n’ont pas encore été chargés dans le processus live. La capture du tick établit l’appel et la forme de sortie, pas sa qualité sémantique.

## Prochaine tranche de l’audit

Poursuivre le lien causal, au-delà du compteur global : suivre un même identifiant d’exécution depuis le slow-cycle et le module qui agit, vers la mutation du planner/registre d’effets, puis vers la lecture qui la confirme. La provenance doit rester bornée et explicite; une sortie de module sans identifiant de tour/cycle ne doit pas être attribuée à un échange utilisateur. Auditer ensuite les scénarios mémoire/contexte, mise à jour des objectifs, et évaluation/expérimentation avec les mêmes critères entrée → sorties requises → mutation → récupération ultérieure. Lumina reste en marche; validation live des correctifs cumulés réservée au redémarrage final.

**Git à ce point de l’audit :** le commit local le plus récent est `cfe6ddf`; `origin/main` demeure sur `17ae81c`. Les corrections décrites dans la section suivante sont encore locales et seront commitées avec les seuls fichiers d’audit ciblés.

> Mise à jour du 11 novembre : les sections précédentes décrivent l’état au moment de leur rédaction. Les commits locaux suivants ont depuis été créés : `1d0d94f`, `cfe6ddf`, `a60be72`. Ils ne sont pas encore chargés dans le processus Lumina en cours; aucun redémarrage n’a eu lieu.

## Provenance de l’action autonome jusqu’au ledger — correction locale

L’audit du chemin `InternalLoop → GoalActionExecutor → ConsequenceTracker → CausalLedger / LongHorizonPlanner` a montré que le tracker savait déjà accepter `cycle_id`, mais que l’exécuteur ne le transmettait pas. Le ledger retrouvait ensuite la prédiction par le dernier couple but/action, ce qui pouvait relier le résultat au mauvais événement si l’ordre des événements changeait. Les résultats du planner n’enregistraient pas l’identité de l’action qui les avait causés.

Correction locale : chaque action reçoit un `execution_id`; le cycle de l’InternalLoop est transmis à l’exécuteur et à la prédiction; le résultat synchrone ou asynchrone transporte les mêmes identifiants; le planner les conserve dans `last_outcome`. Les événements du ledger référencent l’identifiant exact de prédiction/exécution. La chaîne parentale est maintenant **prediction → outcome → error → update**, plutôt que quatre événements rattachés en parallèle à la prédiction. Aucun `turn_id` utilisateur n’est inventé pour une action autonome.

Test de preuve : `tests/test_consequence_execution_provenance.py` vérifie le cycle, l’identifiant commun et la chaîne exacte. `tests/test_intention_planning.py` vérifie que le planner persiste la provenance. Résultat du lot `test_consequence_execution_provenance`, `test_intention_planning`, `test_module_tick_log`, `test_goal_engine_execution_order` : **49 passed**, 7 avertissements Pydantic préexistants; `py_compile` et `git diff --check` réussis. Ce résultat démontre la cohérence locale du chemin de code testé, pas encore le comportement du processus déjà démarré.

Le dernier commit de la reprise est `1d0d94f`. Le processus Lumina reste actif et non redémarré. La suite de l’audit examinera si les effets mémoire/objectif hors ConsequenceTracker ont eux aussi des reçus de mutation/relecture, et si les traces par tour exposent une association vérifiable vers ces effets.

## Reçu persistant pour l’effet sur le GoalEngine — correction locale

La chaîne autonome se terminait dans le ledger et le planner, mais `GoalActionExecutor` incrémentait aussi `Goal.actions_taken` et le gate d’action externe via `GoalEngine.mark_action()` sans enregistrer l’ID d’exécution. Un compteur GoalEngine pouvait donc changer sans reçu local permettant de le rapprocher de l’action. En outre, la méthode ignorait l’échec de sauvegarde : l’état mémoire restait modifié alors que le JSON persistant pouvait être ancien.

Correction locale : le GoalEngine conserve le dernier type d’action, son `execution_id`, son `cycle_id`, son horodatage, ainsi que l’ID du tour (ou de la pensée) qui a créé le but. Les appels de l’exécuteur transmettent les identifiants d’exécution/cycle. Si la persistance échoue, `mark_action()` restaure les compteurs et le reçu en mémoire et renvoie `False`; les actions synchrones exposent séparément `goal_state_persisted`, sans confondre l’exécution de l’action et sa comptabilisation durable. La prédiction et chaque événement causal transportent l’origine du but sous les champs `goal_source_turn_id` / `goal_source_thought_id`, qui indiquent l’origine du but, pas le tour courant de l’action.

Vérification : le test de provenance contrôle la relecture après reconstruction d’un GoalEngine et le rollback après échec de sauvegarde; le test ledger vérifie que les IDs source suivent chaque lien causal. Lot ciblé : **51 passed**, 7 avertissements Pydantic préexistants; `py_compile` et `git diff --check` réussis. Correctif encore local, pas chargé dans le processus courant.

## Effets de conséquence surévalués — correction locale

Le registre d’actions associait `user_question` à `external_feedback`, mais l’opération ne fait que remplir la file de questions; elle ne reçoit aucune réponse. La résolution immédiate déclarait donc un feedback positif, nudgait `relational_memory` et envoyait une mise à jour au modèle de conséquences avant toute réponse humaine. De même, `self_question` était nommé `clarity_gain`, alors que son test mesurait seulement une réponse qui passait des heuristiques et la sauvegarde d’un belief n’était pas vérifiée.

Correction locale : les labels décrivent maintenant des effets opérationnels (`question_queued`, `candidate_insight_persisted`, `research_item_queued`, etc.) et le scope enregistré dit explicitement que le bénéfice cognitif n’est pas établi. `user_question` n’écrit plus dans l’attention relationnelle ni dans le PCM; sa résolution signifie uniquement que la question a été mise en file. Une `self_question` compte comme persistée seulement si `DataAccess.save_belief()` réussit et si la relecture retrouve exactement la déclaration; sinon l’action est finalisée en échec. Cela ne prouve pas encore que le belief est vrai ou apporte de la clarté, ce qui demande une mesure indépendante.

Résultat : les tests de provenance/action et de planification passent à **53 passed**, 7 avertissements Pydantic préexistants; `py_compile` et `git diff --check` réussis. Correction locale en attente de commit; pas encore chargée par Lumina.

## Publication prématurée et preuve d’effet incomplète — correction locale

Le chemin `self_question` diffusait le texte du LLM dans le GlobalWorkspace avant les contrôles de longueur, de sémantique et de grammaire. Un candidat ensuite rejeté pouvait donc déjà influencer les consommateurs en aval. Autre défaut : une exception pendant la sauvegarde/lecture du belief était seulement journalisée; la coroutine pouvait continuer et finaliser l’action comme réussie sans preuve de persistance. Enfin, `_add_thought()` tentait d’appeler `ThoughtStream.add()`, méthode absente : les appels de mémoire, recherche et introspection n’étaient donc pas enregistrés dans le flux annoncé.

Corrections locales : la publication de l’introspection est déplacée après validation et relecture exacte du belief; une exception de persistance finalise explicitement l’action en échec. `ThoughtStream.add()` existe maintenant comme API publique, valide contenu et priorité, inscrit la pensée dans le buffer et la rend récupérable après flush/redémarrage en conservant `thought_type` et `topic`. `_add_thought()` rapporte séparément l’acceptation par le flux et par le workspace; ces effets sont joints au reçu de réussite de `self_question`.

Tests ciblés : `tests/test_goal_action_thought_publication.py`, `tests/test_consequence_execution_provenance.py`, `tests/test_intention_planning.py`, `tests/test_module_tick_log.py`, `tests/test_goal_engine_execution_order.py`, `tests/test_goal_completion_deadlock.py` : **56 passed**, 7 avertissements de dépréciation Pydantic préexistants. Le test vérifie l’ajout, la relecture après persistance et le rapport d’acceptation des deux consommateurs. Cela valide le contrat local, mais pas encore chaque variante d’erreur du fournisseur LLM ni l’effet live après redémarrage.

**Processus :** Lumina n’a pas été redémarré. Le code corrigé reste local et sera évalué sur le processus après l’unique redémarrage final prévu. L’audit continue sur d’autres scénarios et effets aval.

## Replis asynchrones sans attribution — correction locale complémentaire

Les erreurs ou résultats vides de `web_search` et `bisociative_hypothesis` déclenchaient directement une coroutine `self_question` dans le même flux. Cette action secondaire n’avait ni prédiction autonome ni `execution_id` propre; ses résultats pouvaient être attribués à la mauvaise étape du planner ou rester sans provenance. Le chemin dédupliqué de `self_question` marquait également une réussite depuis `_recent_insights` en mémoire, sans relire le belief persistant; le tracker, lui, ne reconnaissait pas cette réussite faute de preuve.

Correction locale : chaque repli `self_question` est maintenant verrouillé comme action distincte, reçoit son propre `execution_id` et une prédiction de conséquence, conserve le cycle et porte `parent_execution_id` dans tous les événements du ledger. Si une introspection identique est déjà en cours, le repli ne la duplique pas. La déduplication n’est considérée réussie que si une relecture retrouve un belief persistant non vide; le reçu expose `belief_persisted=true` et `reused_existing_insight=true`. Les chemins de finalisation transportent les identifiants explicites de l’action qui s’est réellement achevée.

Vérification : le test causal contrôle que la référence d’action parente est conservée sur chaque événement de la chaîne. Lot ciblé : **56 passed**, 7 avertissements Pydantic préexistants; compilation et `git diff --check` réussis. Le test direct du helper asynchrone de repli n’est pas inclus dans ce lot; la liaison est couverte par la compilation, le contrat de tracker/ledger et les tests de planification, et reste à vérifier en live.

**Processus :** toujours aucun redémarrage. Ces corrections locales ne sont pas chargées dans Lumina; l’unique redémarrage reste réservé à la fin de l’audit.

## Échec de comptabilisation qui interrompait la clôture — correction locale

Le reçu GoalEngine était un effet secondaire distinct du résultat de l’action. En async, `mark_action()` n’était pas protégé : une exception pouvait interrompre la finalisation avant la résolution du tracker et du planner. En synchrone, une exception identique pouvait sortir de `run_tick`. À l’inverse, son retour `False` était facile à confondre avec l’échec de l’action elle-même.

Correction : l’écriture du reçu GoalEngine passe par une fonction isolée qui capture l’exception, rapporte si le reçu a été persisté et laisse le résultat opérationnel réel continuer vers la clôture. Le reçu renvoyé par la finalisation async expose les deux états. Le ledger enregistre séparément `success` et `goal_state_persisted`, ainsi que les preuves de persistance du belief et d’acceptation des consommateurs de pensée. Le résultat n’affirme donc pas que la comptabilisation interne a réussi quand elle a échoué.

Vérification locale : un test simule une panne d’écriture GoalEngine; le test de ledger vérifie que succès opérationnel, persistance du belief et échec de persistance du compteur restent distincts. Le lot ciblé atteint **57 passed**, 7 warnings Pydantic préexistants; `py_compile` et `git diff --check` sont propres. Le test passe sous `PYTHONUTF8=1`, requis dans cette console Windows pour les impressions Unicode de configuration.

**État live :** aucun redémarrage effectué; le processus actif n’a pas ces corrections en mémoire. Le cycle final de redémarrage reste reporté jusqu’à la fin de l’audit.

## Sorties transmises aux consommateurs — preuve ajoutée

Le rappel mémoire, la recherche Web et l’hypothèse associative produisaient du contenu, mais le reçu ne distinguait pas la création du contenu de son acceptation par le flux de pensées et le workspace. Le résultat de mémoire ne remontait pas ces deux acceptations; les actions asynchrones les ignoraient également.

Les rapports d’action conservent maintenant les deux booléens issus de `_add_thought()`. Les événements `outcome` du ledger sélectionnent les preuves pertinentes : persistance du belief, pensée enregistrée, broadcast workspace accepté/refusé, résultat de recherche mis en file et hypothèse générée. Le test vérifie qu’un workspace qui refuse un broadcast reste distinct d’un ThoughtStream qui l’a accepté; les valeurs ne sont pas fusionnées en un statut générique « réussi ».

Le lot ciblé reste à **57 passed**, 7 warnings Pydantic; `py_compile` et `git diff --check` réussis. Cela augmente l’observabilité des effets, sans démontrer encore que les sorties sont sémantiquement pertinentes ni qu’un consommateur particulier les a utilisées.

## Prédictions orphelines quand le LLM diffère une action — correction locale

Lorsque le créneau LLM était occupé, l’exécuteur retirait sa prédiction locale pour ne pas comptabiliser un échec. Le `ConsequenceTracker` gardait pourtant la prédiction dans son dictionnaire `_pending`; elle gonflait `n_predictions` et laissait le rapport de fermeture sans résolution correspondante. Les métriques pouvaient donc confondre une action jamais exécutée avec une action exécutée sans effet.

Correction : `ConsequenceTracker.cancel()` ferme explicitement une prédiction non exécutée, retire son état pending et écrit un événement `deferred` rattaché à la prédiction, sans erreur, feedback ou mise à jour d’efficacité. `_defer_async_action()` appelle désormais cette fermeture. Le rapport expose `n_cancelled`, `n_pending`, `eligible_predictions` et calcule le taux de résolution sur les prédictions d’actions effectivement engagées.

Le test vérifie la chaîne `prediction → deferred`, l’absence de faux échec, zéro prédiction pending et le dénominateur excluant l’action annulée. Le lot ciblé passe à **58 passed**, 7 avertissements Pydantic préexistants; compilation et `git diff --check` réussis. Le processus Lumina n’a toujours pas été redémarré.

## Sortie partielle avant contrôle de sécurité — correction locale

L’audit de la fermeture de tour a trouvé un défaut de séquencement : le chemin principal envoyait chaque fragment de réponse pendant la génération, alors que `check_output()` n’était appelé qu’une fois la réponse complète reçue. Remplacer ensuite la réponse finale ne pouvait pas retirer les fragments déjà transmis. En plus, l’historique LLM était écrasé avec le texte brut avant le contrôle; après un remplacement, l’historique pouvait donc diverger de la réponse effectivement remise.

Correction locale : le texte de réponse est maintenant accumulé sans émission pendant la génération; après le contrôle de sortie, un seul texte final est émis. L’historique assistant est mis à jour après le même contrôle, pour conserver la réponse autorisée/remplacée. Les événements de raisonnement restent sur leur canal distinct et ne sont pas comptés comme texte de réponse. Si le contrôle de sortie lève une exception, le chemin échoue avant d’émettre le texte final.

Une régression AST vérifie que le seul `yield raw_response` se trouve après `check_output()` et qu’aucun fragment du fournisseur (`token`, `before`, `after`) n’est remis directement. Vérification locale : **89 passed**, 3 sous-tests passés, 9 avertissements existants sur le lot de tour, workflow, auto-description, action/pensée, provenance et planification; compilation Python réussie. Le changement de latence est délibéré : la réponse visible attend maintenant la fin du contrôle de sortie, mais le texte peut encore être diffusé avant la fin des apprentissages post-tour.

**Limite de preuve :** `output_safety` est facultatif; lorsque le moteur n’est pas initialisé, la trace reste explicitement `skipped_unavailable` et la réponse est remise en pass-through. Ce correctif garantit le séquencement du contrôle disponible, pas la qualité sémantique du modèle de règles ni une validation cognitive de la réponse.

**Processus et Git :** pas de redémarrage de Lumina. Cette tranche est vérifiée localement et sera commitée séparément; elle ne sera pas chargée dans le processus courant avant le redémarrage final. L’audit continue.

## Évaluation de sécurité transformée à tort en autorisation — correction locale

Le contrat du module `AsimovConstraints` annonçait un comportement fail-safe, mais ses deux méthodes `check_input()` et `check_output()` capturaient leurs exceptions puis renvoyaient `_OK`. Le nouveau préfiltre avant les routes GoalEngine/Body ne pouvait pas fermer ce défaut : une exception interceptée à l’intérieur du module ressemblait à une validation réussie. Le même fail-open pouvait laisser passer un texte généré si le contrôle de sortie rencontrait une erreur.

Correction : `ConstraintResult` porte maintenant `evaluation_error`. Les erreurs d’évaluation produisent un résultat bloquant avec un texte sûr et un reçu d’audit `evaluation_error:<type>`. Le chemin d’entrée distingue cet état d’un blocage de politique normal et termine le tour en échec avant toute route déterministe. Le chemin de sortie remplace le texte généré et marque l’étape `output_safety` en échec; il ne livre pas le contenu non vérifié. Les appels de compatibilité reçoivent également le résultat bloquant, sans dépendre d’une exception qui pourrait être interceptée plus loin.

Vérification locale : tests d’injection d’une panne dans les évaluateurs d’entrée et de sortie, régression d’ordre avant mutations Goal/Body, preuve de fermeture du tour et événements de chat : **29 passed, 6 sous-tests**, 9 avertissements de dépendances existants. `py_compile` et `git diff --check` réussissent. Ces tests valident le comportement du code local sous panne simulée; le processus Lumina actif n’a pas encore chargé ce changement.

**État live :** aucun redémarrage. La vérification intégrée des étapes et des sorties réelles reste réservée au redémarrage unique de fin d’audit.

## Chemins déterministes et repli hors du contrôle de sortie — correction locale

Le parcours des retours anticipés a révélé deux autres écarts au contrat du tour. Les réponses GoalEngine et Body étaient émises sans `check_output()`; le validateur ne demandait ni preuve du contrôle d’entrée ni preuve du contrôle de sortie pour ces chemins. En cas d’échec du flux principal, le fallback bloquant faisait un second contrôle d’entrée sans tracer son résultat, puis contrôlait la sortie avant livraison mais ne consignait pas la génération de fallback, le contrôle ni la réponse finale. L’historique assistant pouvait rester différent du texte effectivement livré.

Correction : les réponses GoalEngine et Body passent maintenant par un contrôle de sortie partagé avant enregistrement de l’échange et livraison. Les routes déterministes exigent dans leur intégrité de trace les étapes de sécurité d’entrée et de sortie ainsi que leur ordre. Le fallback s’appuie sur le contrôle d’entrée central déjà effectué pour ce tour (il ne le répète pas), enregistre `fallback_generation`, passe la réponse par le contrôle de sortie partagé, aligne l’historique avec le texte approuvé, puis clôture avec les reçus de finalisation et de réponse. Le validateur expose `blocking_fallback` et vérifie les preuves spécifiques de cette route.

Tests ciblés : sorties déterministes bloquées/remplacées, erreur d’évaluation, ordre des vérifications et intégrité du fallback, avec les tests de sécurité, transactions GoalEngine, preuve Body, preuve de tour et événements UI : **33 passed, 6 sous-tests**, 9 avertissements de dépendances préexistants. `py_compile` et `git diff --check` réussissent. La persistance d’un objectif reste gouvernée par le contrôle d’entrée avant mutation; le contrôle de sortie valide la confirmation adressée à l’utilisateur après la transaction.

**État live :** Lumina n’a pas été redémarré; aucune de ces nouvelles étapes n’est encore présente dans le processus actif.

## Repli de chat sans contexte live — correction locale

Le chemin principal injecte les observations courantes du Body, de la caméra PC et de la Cognitive Trace dans le flux cognitif. Si ce flux échouait, le fallback historique appelait `AI_SYSTEM.get_response()` avec seulement le texte utilisateur. Pour une question sur le Body ou la caméra, le modèle pouvait alors produire une réponse fluide sans les observations qui auraient dû la justifier; pour une question de trace, il n’avait pas le snapshot affiché. Le chat classique transmet aussi une observation PC à chaque tour lorsque la perception autonome est active, donc bloquer le fallback sur la seule présence de cette observation aurait également interrompu des conversations sans rapport.

Correction locale : avant le fallback sans contexte, le tour est classé selon son besoin d’observations Body, caméra ou Cognitive Trace. Si une de ces sources est nécessaire, le fallback LLM est refusé; Lumina indique explicitement que le flux a échoué et qu’aucune observation live n’a été vérifiée. La présence d’une observation caméra en arrière-plan ne suffit pas, à elle seule, à bloquer les tours ordinaires. Le refus passe encore par le contrôle de sortie et reçoit des étapes de fallback, finalisation et réponse, puis la trace se termine avec `status=failed` et une erreur terminale attribuable.

Vérification locale : le garde-fou précède l’appel natif `get_response`; les régressions AST vérifient les besoins Body/caméra/trace, le cas d’une vision de fond et la clôture explicite en échec. Lot ciblé : **93 passed, 9 sous-tests**, 9 avertissements de dépendances préexistants; `py_compile` et `git diff --check` réussissent. Pendant la collecte, l’extension native FAISS a imprimé une exception Windows `0xc0000008` sur stderr; pytest a néanmoins terminé avec code 0 et résumé vert, anomalie à suivre séparément.

**État live :** aucun redémarrage. Le processus courant n’a pas chargé ce correctif; la vérification intégrée reste réservée au redémarrage final.

## Méta-événement terminal avant clôture et verrou — correction locale

Les interfaces chat et la boucle proactive s’arrêtaient dès réception de `__meta__`. Or plusieurs branches ne clôturaient la trace qu’après ce `yield`; la trace pouvait donc rester ouverte. Le wrapper `get_response_stream()` suspendait aussi le générateur à l’intérieur du verrou global de tour pendant qu’il livrait ce méta-événement. Un consommateur qui s’arrête à cet événement pouvait retarder la libération du verrou, donnant l’impression que les tours suivants étaient bloqués. Dans le chemin LLM, la validation externe réécrivait en plus l’étape `response` déjà fingerprintée avec une entrée minimale, supprimant la preuve de sortie.

Correction : les branches GoalEngine, Body et fallback finalisent les reçus avant leur méta-événement. Le chemin stream marque la fin de vie du tour avant de transmettre le méta-événement et conserve le fingerprint `response` produit par le lifecycle interne. Le wrapper garde le méta-événement terminal en attente, draine le générateur interne, sort du verrou, puis livre le méta-événement. Les consommateurs chat/proactif de la page principale continuent jusqu’à l’épuisement du générateur au lieu de rompre après le méta-événement.

Vérification ciblée : preuve AST de l’ordre clôture→terminal, drainage des consommateurs et libération du verrou avant livraison : 19 tests passent. Lot élargi sur le flux terminal, sécurité, preuve de tour, GoalEngine, Body, workflow et journal des ticks : **91 passed, 9 sous-tests**, 9 avertissements de dépendances préexistants. `py_compile` et `git diff --check` réussissent. Durant la collecte élargie, FAISS a aussi écrit un diagnostic natif Windows `0xc0000008` sur stderr; pytest a néanmoins terminé avec le code 0 et un résumé vert. Il est enregistré comme anomalie de l’environnement de test, non comme résultat Lumina.

**État live :** pas de redémarrage. Ces correctifs restent du code local non chargé par le processus actuel.

## Route fast déléguée comptée à tort comme génération — correction locale

La validation du pipeline acceptait `fast_first_pass=delegated` comme preuve qu’une réponse avait été générée. Or `delegated` n’est qu’une décision de routage : si le provider principal ne termine pas, la trace pouvait déclarer le cœur du tour complet sans génération primaire ni texte de réponse attribuable. La route directe `selected_direct` reste valide comme chemin alternatif; une délégation exige désormais `primary_generation=completed`.

Vérification : régression qui construit une trace déléguée sans génération et exige `incomplete_evidence` avec l’étape `generation` manquante. Le lot élargi couvrant ces chemins ainsi que mémoire, flux cognitifs, sélection de pensée, raisonnement moyens/buts et transactions d’objectifs passe à **159 passed**, 14 sous-tests, 9 avertissements. Compilation et `git diff --check` réussissent. Pas de redémarrage live; les correctifs restent locaux.

## Consommateur du chat classique incompatible avec les événements structurés — correction locale

Le flux PersonaBridge peut émettre des dictionnaires d’événement (`reasoning`, sources Web) avant la réponse méta. L’API HTTP les distingue, mais le consommateur de la page de chat classique concaténait chaque élément à `accumulated_text`; un dictionnaire reçu déclenchait un `TypeError` et interrompait le tour. Le vérificateur proactif, lui, ignorait déjà les événements non méta.

Correction : la page classique prend maintenant uniquement les chaînes comme texte de réponse, traite le dictionnaire méta comme clôture du tour et ignore les événements auxiliaires/non textuels au lieu de les afficher ou de casser le flux. Une régression AST cible précisément la boucle qui met à jour la bulle de réponse et impose le `continue` avant la concaténation.

Vérification cumulée : **160 passed**, 14 sous-tests, 9 avertissements existants; compilation des fichiers modifiés et `git diff --check` réussis. Le test d’intégration live avec le modèle n’a pas encore eu lieu et attend le redémarrage final. Lumina reste actuellement en marche.

## Point de reprise avant redémarrage final

Les quatre dernières corrections de ce cycle sont commitées localement, dans cet ordre :

- `74157ee` — l’échec d’évaluation de sécurité bloque au lieu d’autoriser.
- `b038cbb` — les réponses déterministes et le fallback passent par le contrôle de sortie.
- `2688e97` — clôture de trace, drainage du flux et libération du verrou avant l’événement terminal.
- `180523d` — aucune réponse Body/caméra/trace via un fallback dépourvu du contexte live requis.

Le lot de régression le plus récent passe : **93 tests, 9 sous-tests**; compilation et contrôle de diff réussis. Il reste 9 avertissements de dépendances connus et le diagnostic natif FAISS Windows `0xc0000008` durant la collecte, sans échec pytest.

**À faire après le redémarrage unique demandé :** interroger le endpoint de santé et l’API de trace du Brain; vérifier un tour ordinaire puis un tour Body/caméra avec contexte disponible; provoquer un échec de streaming sur une question contextuelle si cela peut être fait sans perturber le modèle; contrôler chaque identifiant de tour, les sources injectées, les étapes de sécurité/génération/finalisation et les événements finaux. Confirmer que la conversation ordinaire conserve son historique en fallback, que les questions contextuelles échouent explicitement si leur flux échoue, et que le verrou est libéré après chaque tour.

**Autres points d’audit encore ouverts :** vérifier la continuité d’historique après un fallback natif; contrôler la qualité des réponses et leurs effets aval sur plusieurs scénarios représentatifs; classer les modules sans tick/indisponibles selon leur rôle et preuves observables; isoler l’anomalie FAISS; compléter ensuite l’audit des chemins de génération et des consommateurs, sans confondre tick d’un module et effet causal prouvé.

**Processus :** Lumina n’a pas été redémarré. Le code local est prêt pour le contrôle live au redémarrage final; aucune conclusion d’intégration runtime n’est encore revendiquée.

## Reprise live après redémarrage — blocage de l’auto-calibration corrigé localement

Le socket local a répondu après le redémarrage (`/status`: Brain prêt, modèle LM Studio actif; interface prête et non occupée). Un tour d’audit non moteur a été exécuté avec l’identifiant `1bf4836f-bd69-4f3a-8a75-2af4d0950f88`. La trace serveur compte 62 étapes, `pipeline_integrity=consistent`, zéro étape manquante/échouée et une réponse finalisée; les étapes conditionnelles non applicables sont explicitement marquées. Cela prouve l’exécution du chemin de chat pour ce tour, pas la qualité sémantique du texte ni l’usage de tous les modules à chaque tour.

La lecture live du `CognitiveAuditEngine` a ensuite montré 50 snapshots, aucun essai et aucune tentative de proposition enregistrée à ce relevé. Le relevé suivant a exposé la cause exacte : `llm_error: EnhancedAISystem.get_response() got an unexpected keyword argument 'messages'`. Le moteur appelait la façade conversationnelle avec l’API du modèle bas niveau; chaque génération de proposition échouait donc avant de créer un essai, malgré un signal `mean_skill_depth` durablement sous sa cible.

Correction locale : les propositions de calibration utilisent maintenant `EnhancedAISystem.llm.get_response(messages, max_tokens, temperature)`, l’adaptateur bas niveau configuré. La façade conversationnelle n’est pas appelée pour cette opération interne. Une régression vérifie l’API utilisée, interdit l’appel de la façade et confirme qu’une proposition valide est effectivement produite dans les bornes du paramètre.

Vérification locale : `tests/test_health_data_regressions.py` — **11 passed**; `py_compile` et `git diff --check` réussissent. Le processus live n’a pas été redémarré, donc la correction n’est pas encore chargée ni validée par le prochain cycle d’audit du modèle.

**Suite immédiate :** commit/push de cette correction ciblée, poursuivre l’inspection du workspace et des effets d’objectifs pour identifier la provenance du but narratif de faible qualité observé live, puis demander un redémarrage seulement lorsque le lot de corrections brain-only prêt à vérifier sera réuni.

## Provenance des croyances de soi et objectifs — correction locale

L’inspection des enregistrements live a relié les modules et leurs effets : `SemanticGraphCleaner` promeut des hubs de fréquence/connectivité sous la catégorie `semantic_concept`; une ancienne version du `BeliefBootstrapper` les a recopiés dans `identity.json` avec le préfixe `expressed_`; ces records sont ensuite apparus comme croyances dans `self_concept.json`, avec 11 violations et 0 affirmation; `generate_identity_topic()` a interprété ce ratio comme un conflit de comportement réel; `GoalQualityFilter` a alors produit le topic d’un objectif d’identité depuis cette phrase. Le score d’alignement sémantique a validé le thème « identité » sans vérifier que sa source était une statistique de graphe.

Correction locale : ajout d’une classification partagée par provenance (`semantic_concept` et marqueur legacy `semantic_hub_*`), exclusion de ces records lors du bootstrap et de la synchronisation, mise en quarantaine des anciennes entrées dans le self-model avec conservation de leur contenu pour audit, et exclusion du générateur d’objectifs d’identité. Le bootstrapper normalise aussi le préfixe `expressed_` une seule fois. Enfin, `GoalQualityFilter` migre le topic déjà persisté pour l’objectif généré par le système; l’ancien topic est conservé dans `topic_history` avec le motif et l’horodatage.

Vérification locale : **59 passed**, 11 sous-tests, 9 avertissements connus sur le lot provenance, goals, mémoire, registre d’exécution et audit cognitif; `py_compile` et `git diff --check` réussissent. La correction n’est pas chargée dans Lumina; le redémarrage final reste nécessaire pour constater la quarantaine et la migration dans les données actives.

## Les séries de sous-performance sont interrompues par les échantillons absents

Le snapshot live marquait `experiment_confirmation_rate` et `question_resolution_rate` indisponibles alors que `consecutive_under` conservait pour ces signaux une valeur de 293. `_update_consecutive_underperformance()` ne parcourait que les valeurs présentes; une période sans observation ne rompait donc pas la série, et une mesure revenue plus tard pouvait satisfaire artificiellement la règle des deux audits consécutifs.

Correction : tout signal absent du snapshot remet maintenant son compteur de série à zéro; les signaux mesurés continuent leur série normalement. Régression ajoutée couvrant un signal encore mesuré et sous la cible ainsi que deux signaux absents avec anciennes séries positives.

Vérification locale : **60 passed**, 11 sous-tests, 9 avertissements préexistants; compilation et `git diff --check` réussis. Cette correction est locale et attend son commit/push; elle requiert le même redémarrage groupé pour validation live.
