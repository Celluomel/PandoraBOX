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

À l’état actuel de cette reprise, `main` contient les commits d’audit jusqu’à `7e7835e`, tandis que `origin/main` reste sur `17ae81c` (avance locale, pas encore poussée). Le worktree contient des modifications et fichiers non suivis préexistants sans rapport avec l’audit, notamment des changements Body, pages, tests et artefacts. Ils restent intacts et exclus des commits d’audit.

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
