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

## Vérification après reprise du socket et suites cognitives — 11 novembre

L’accès local au Brain a été rétabli via le socket autorisé. `/status` indique `ready=true`, uptime ~3 742 s, modèle `lmstudio/gemma-4-e4b-uncensored-hauhaucs-aggressive`; `/api/interface/status` indique l’interface prête, `busy=false`. Le endpoint `/api/interface/cognitive-health` répond aussi. Il rapporte encore l’ancienne tentative `llm_error: EnhancedAISystem.get_response() got an unexpected keyword argument 'messages'`, sur le cycle 9600; ce processus n’a pas été redémarré depuis les commits qui corrigent l’adaptateur, donc cette entrée est un résultat historique, pas une exécution du code corrigé. Le relevé courant compte toujours zéro essai, et `experiment_confirmation_rate` / `question_resolution_rate` restent indisponibles. Cela signifie qu’il n’existe pas encore de résultats réels permettant de juger ces deux dimensions; les laisser indisponibles est préférable à inventer un taux nul.

Deux lots de tests cognitifs ont été exécutés avec l’environnement virtuel du dépôt : **46 tests + 7 sous-tests** couvrant santé, intégrité du workflow, traçage de tour, provenance des croyances et exécution d’objectifs; puis **48 tests** couvrant sélection pensée→objectif, sémantique et ordre GoalEngine, publication d’actions, transaction d’objectif, langage d’identité et limites d’identité. Total : **94 tests et 7 sous-tests réussis**. Les 9 avertissements sont des dépréciations/avertissements de dépendances déjà présents. Aucun test de matériel ou de Body n’est inclus.

Les corrections de cette tranche sont déjà sur `origin/main` : `104ee0b` (adapter LLM interne de l’auto-audit), `aef2112` (provenance des hubs sémantiques empêchant les faux objectifs d’identité), `2c6be67` (réinitialiser les séries lorsque les mesures manquent). Les autres changements locaux préexistants restent intacts et ne sont pas inclus.

**Conclusion intermédiaire :** les défauts logiciels identifiés ont des régressions vertes, et le chemin de chat live reste sain; en revanche, le processus actif ne peut pas encore prouver les correctifs récents ni produire un essai d’auto-calibration. Étape suivante : redémarrage unique par l’utilisateur pour charger `origin/main`, puis contrôler qu’un cycle d’audit enregistre une nouvelle tentative (pas l’erreur historique), que le LLM produit une proposition bornée ou un motif d’échec explicite, et que la trace de tour lie les sorties aux effets réellement observés. Aucun verdict global sur la qualité cognitive n’est revendiqué.

## Vérification live après redémarrage : essai actif sans lien causal — correction suivante

Après le redémarrage, `/status` confirme Brain prêt avec Gemma; l’interface est prête et le verrou est libre. Le tour non moteur `fb6929e7-7e92-49cb-b628-a0bd40119372` a terminé avec événements `Turn started` puis `Turn completed`; la réponse cite les preuves de trace (`self_description_context`, assemblage du prompt, manifeste de ticks et génération primaire). Cela confirme un tour de chat génératif terminé et attribuable, sans valider la justesse générale de ses modules.

Au cycle d’audit 9640, le défaut de l’adaptateur est résolu : le moteur a produit et activé un essai. L’analyse du dossier live a toutefois exposé une erreur de conception plus grave : `CognitiveAuditEngine` laissait le LLM choisir librement parmi six paramètres, sans correspondance entre paramètre et signal mesuré. Le système a donc appliqué `grounding_boost` de 0,030 à 0,039 pour corriger `mean_skill_depth` de 0,30, alors que ce paramètre augmente la confiance de croyances validées et ne fait pas progresser les compétences vérifiées. La proposition était bornée numériquement, mais son hypothèse de cause à effet n’était pas fondée. Le statut disait aussi zéro essai pendant qu’un essai était actif, parce que le compteur ne comptait que les essais terminés.

Correction ajoutée : les propositions sont désormais limitées à une table explicite mesure→paramètres causaux; le seul couple actuellement justifié est `belief_confidence_mean`→(`grounding_boost`, `decay_rate_base`). Les signaux sans paramètre directement relié restent mesurés, mais ne provoquent aucun changement exploratoire; le moteur enregistre `no_causally_mapped_parameter`. Toute réponse LLM qui nomme un paramètre hors de la table est rejetée. Au chargement, un essai persisté incompatible est restauré à sa valeur antérieure, archivé avec `rejected_causal_mismatch`, et retiré de l’état actif. Le statut distingue désormais les essais terminés, actifs et les signaux non actionnables.

L’essai live `mean_skill_depth`→`grounding_boost` est encore dans le processus courant et doit être restauré au prochain chargement par cette migration; je ne prétends pas que la mutation a déjà été annulée dans le processus actif. Les tests vérifient l’absence d’appel LLM pour un signal non mappé, le rejet d’un mauvais paramètre, le rollback d’un essai ancien au chargement et le comptage explicite d’un essai actif.

Vérification locale après correction : **98 tests + 7 sous-tests réussis**, incluant les suites audit, provenance, objectifs, identité, mémoire et workflow; `py_compile` et `git diff --check` réussissent. Les 9 avertissements proviennent des dépendances/configurations Pydantic existantes.

**État de l’audit :** le défaut d’appel LLM est validé comme corrigé en live; le défaut de causalité est corrigé dans le code et couvert par les régressions, mais requiert un second redémarrage pour restaurer l’essai actif et confirmer le résultat `trial_reverted_causal_mismatch`. Les taux d’expériences et de résolution restent indisponibles faute de dénominateurs observés; ils ne sont pas convertis en zéros. Le verdict global sur le harnais reste ouvert.

## Contrôle après redémarrage et provenance persistée — 11 novembre

Le redémarrage a confirmé le rollback du test causal actif : le registre live rapporte `trial_reverted_causal_mismatch`, restaure `grounding_boost=0.03`, n’a plus d’essai actif et compte un essai terminé. Le chat génératif a aussi terminé un tour attribué. Ce sont des preuves d’exécution de ces chemins, pas de la qualité générale du harnais.

Le contrôle des fichiers persistés a révélé que la migration précédente ne couvrait pas tout le chemin : `self_concept.json` est désormais sans croyance active dérivée du hub, mais `identity.json` contient encore **42** croyances `expressed_semantic_hub_*` actives sur 200. Aucune nouvelle admission ne devrait les reproduire, mais leur présence dans la source d’identité peut encore les réinjecter lors d’une synchronisation. Le correctif précédent n’était donc pas entièrement concluant.

Correction en cours : le synchroniseur met en quarantaine, sans perte de contenu, les anciennes statistiques sémantiques et les insights explicitement dérivés; il conserve le format dict/liste existant. Le bootstrap et la génération de sujets d’identité ignorent aussi ces deux formes de contamination. Tests ciblés après ajout des cas migration dict/liste : **19 tests passés**; compilation ciblée et `git diff --check` réussis. Une exécution combinée précédente a rapporté **34 tests passés**; FAISS a émis un diagnostic natif Windows `0xc0000008` sur stderr pendant cette collecte, sans empêcher le code retour 0. Cette dernière migration n’est pas encore chargée par le processus Lumina courant.

**Conclusion de cette vérification :** non, toutes les corrections ne sont pas encore validées de façon concluante. Le rollback causal est confirmé live. La provenance de l’identité reste à confirmer après commit/push et un redémarrage supplémentaire : le critère live sera `identity_records_quarantined_by_provenance=42` (ou le nombre réellement restant au moment du cycle), aucun hub/insight dérivé dans les croyances actives, et contenu préservé dans `provenance_quarantine`. Le verdict d’efficacité cognitive globale reste ouvert et nécessite des scénarios représentatifs avec sorties et effets aval attribuables.

## Audit mémoire et profil utilisateur — défauts établis, correctifs locaux

Le chemin de réponse récupère les mémoires FAISS/personnelles/visuelles/événementielles avant la génération, puis les injecte comme candidats dans le prompt. La trace précédente ne conservait que le nombre d’éléments; elle ne permettait donc pas de vérifier quels candidats ont été offerts au modèle. Nouveau reçu de provenance : empreinte de la requête, références hachées des candidats, tier/type/source et présence d’horodatage; aucun texte de mémoire n’est copié dans la trace. `prompt_assembly` référence désormais les étapes `memory_retrieval` et `user_profile_context`. Cela prouve l’offre du contexte au LLM, pas que le LLM s’est appuyé sémantiquement sur chaque souvenir; une attribution de réponse au souvenir nécessite encore une évaluation de sortie.

Le profil explicite est lu via `UserManager.prompt_context_for()` au montage du prompt, puis `learn_from_message()` est appelé après la réponse, uniquement pour les tours humains. Le profil comportemental de `WorldModel.update_from_interaction()` est un mécanisme distinct. L’audit a trouvé qu’il était appelé aussi pour les tours pairs; il est désormais explicitement ignoré sur un tour FLUX et son reçu (`updated`, `skipped_by_scope`, `unavailable` ou `failed`) est attaché à la Cognitive Trace. Le reçu précédent d’apprentissage ne rapportait qu’un booléen et ne distinguait pas absence de fait explicite, doublon, profil invité ou modification réelle. Il rapporte maintenant un statut et les catégories modifiées, sans révéler les valeurs personnelles; une étape `user_profile_context` atteste l’injection ou son absence.

Inspection persistée : le profil Fred contenait plusieurs fragments de tour (« back », « not sure… », « ravi de l’entendre », « curieux de savoir… ») dans `characteristics`, donc ces phrases pouvaient être réinjectées comme traits durables. Le chargeur les met désormais en quarantaine dans `profile_provenance_quarantine`, les conserve, et exclut ces entrées du prompt. L’extraction future rejette les mêmes marqueurs conversationnels. Le contrôle ciblé a d’abord exposé un cas de concaténation sans espace (`de retourcomment…`); le filtre a été élargi, puis la suite du profil passe.

Vérification locale de cette tranche après correction : `test_presence_identity_language.py`, `test_cognitive_log_regressions.py` et `test_health_data_regressions.py` combinées : **44 passed, 4 sous-tests**; 9 avertissements de dépendances préexistants; compilation Python et `git diff --check` réussis. FAISS a parfois émis son diagnostic natif Windows `0xc0000008` durant une collecte antérieure, mais cette dernière exécution n’a pas montré ce diagnostic. Ces modifications sont locales et ne sont pas encore chargées par le Lumina courant.

Le contrôle après redémarrage et le passage SCS mentionnés ci-dessous ont ensuite résolu la migration des croyances d’identité et du profil. Le rappel sémantique reste un critère séparé : succès de retrieval n’équivaut pas à rappel correct.

## Audit live mémoire/profil après redémarrage — 11 novembre

Le Brain et l’interface sont prêts (`/status`: `ready=true`; interface: `ready=true`, `busy=false`), le loop cognitif est vivant et sans erreur observée. Un cycle SCS a été exécuté (`tick_count=1`, `last_status=completed`). La migration persistée a archivé **43** enregistrements d’identité contaminés : `identity.json` contient maintenant 157 actifs, zéro contamination active et 43 en quarantaine. `self_concept.json` reste à 40 actifs sans contamination. Le profil Fred conserve zéro caractéristique éphémère et **8** fragments en quarantaine.

Tour de profil `db84125c-b304-4e2c-9da4-a1bfbda7c46d` : le contexte `user_profile_context` a été marqué injecté; Lumina a répondu correctement « Fred ». Le reçu de profil humain a aussi été produit. Cela confirme la lecture du profil et la génération, mais l’ancienne version live de la trace ne montrait pas le statut/hash du profil ni les valeurs sûres du reçu.

Tour de rappel `4921b8a3-a6e8-4b55-b1f5-c45551336c86` : `memory_retrieval` a terminé, `prompt_assembly` a explicitement consommé son empreinte et celle du profil, puis `primary_generation` a terminé. Pourtant Lumina a donné une réponse fausse à « quelle règle avons-nous définie pour Lumina et Flux ? » : elle a remplacé la décision persistée (Lumina master, Flux child, messages de Lumina vers Flux) par un récit inventé d’échanges initiés par l’utilisateur. C’est un **échec de qualité du rappel**, malgré une exécution réussie de la chaîne. L’ancien reçu prouvait qu’il y avait un résultat de récupération, pas si ses candidats étaient pertinents ni de quel tier/source ils venaient; il n’est donc pas possible d’attribuer cette réponse aux bons souvenirs.

Correction locale en cours : les reçus de trace exposent désormais uniquement `candidate_count`, références hachées, tier/type/source et présence d’horodatage des souvenirs; l’injection du profil expose statut/source/hash; l’apprentissage de profil expose le statut, `changed` et le nombre mis en quarantaine. Les contenus privés restent exclus. Le prompt demande maintenant, pour toute question sur une décision ou un échange antérieur, de répondre uniquement depuis un souvenir pertinent ou l’historique visible, et de déclarer l’absence de rappel plutôt que d’inventer. Tests ciblés : **23 passés**, 4 sous-tests; compilation et `git diff --check` réussis.

**Critère non encore satisfait :** il faut charger ces changements, refaire exactement le tour de rappel et vérifier dans la trace si un candidat pertinent a été injecté. S’il ne l’est pas, le défaut est dans la recherche/ranking; s’il l’est mais que la réponse reste fausse, le défaut est dans l’usage/grounding du LLM. Seul ce test départagera les deux causes. La valeur correcte de la décision a une source vérifiable dans l’historique de conversation fourni par l’utilisateur; aucun verdict positif de mémoire n’est revendiqué.

## Cause du faux rappel confirmée et correction de requête — 11 novembre

Après le redémarrage sur `38a2f02`, le test `d6ed1d51-e460-4f4b-97c0-1b54bdd3dd81` a encore échoué. La trace a montré 8 candidats, principalement visuels ou sans rapport. En recalculant le SHA-256, la requête réellement envoyée à la mémoire était `relationship person ` + la question de l’utilisateur : `Attention.memory_recall_mode()` avait donc réécrit une question de décision technique en requête relationnelle. Les métadonnées candidates confirment l’absence du souvenir pertinent dans ce lot. Le modèle a ensuite ignoré la consigne générale de mémoire et inventé un flux bidirectionnel.

Cause du harnais établie : le biais d’attention modifiait le contenu de recherche au lieu de rester un signal de contexte. Correction locale : le texte utilisateur reste la requête canonique; le mode attentionnel est enregistré séparément dans le reçu. Les candidats exposent aussi leur score de pertinence borné, ce qui permettra de distinguer un lot simplement non vide d’un lot effectivement proche de la requête. La consigne de réponse exige déjà qu’une question historique soit ancrée dans un candidat pertinent ou dans l’historique visible, sinon l’absence de rappel doit être reconnue.

Les deux sondes de chat précédentes ont été persistées par le fonctionnement normal de Lumina dans `ai_system.db`; la première réponse erronée est donc aussi devenue un souvenir. Je ne l’ai pas supprimée ni altérée. Le test suivant doit vérifier que la requête brute remonte une source antérieure fiable et que les anciens propos du modèle ne sont pas traités comme preuve. Tests après correction de séparation requête/attention : **24 passés**, 4 sous-tests; compilation et contrôle whitespace réussis. Le code exige un autre redémarrage avant toute validation live; aucune correction de la pertinence/ranking n’est encore revendiquée.

## Validation live de la requête brute et défaut de provenance des souvenirs — 11 novembre

Après redémarrage, le tour `81870785-b12d-4fa5-9ad4-1c761e35f89f` confirme que la requête mémoire est désormais le texte utilisateur brut (SHA-256 `838114…d0a2`), avec le mode attentionnel `relational` en métadonnée séparée. La chaîne mémoire→prompt→génération a terminé. Le meilleur candidat avait une pertinence de 0,7348, mais correspondait à une réponse Lumina erronée produite par la sonde précédente. La réponse live a repris cette fausse interprétation (« Fred → Lumina → Flux exécute/répond ») au lieu du flux Lumina→Flux. Le défaut de réécriture de requête est corrigé; le rappel n’est toujours pas fiable.

Cause supplémentaire : les souvenirs conversationnels sont fusionnés sous la forme `User: ... | Lumina: ...`; le prompt ne séparait pas assez fortement une question utilisateur, une déclaration utilisateur et une affirmation de Lumina. Le pipeline traitait donc un ancien texte du modèle comme s’il pouvait corroborer une décision. Correction locale : les souvenirs dialogués sont rendus en segments `USER MESSAGE` / `LUMINA REPLY`; une question utilisateur n’établit pas sa propre réponse, et une réponse historique de Lumina n’est pas une preuve de vérité ou d’accord. La trace marque également la présence de segments utilisateur/assistant sans exposer leur texte. Vérification locale : **25 tests passés**, 4 sous-tests; compilation et `git diff --check` réussis. La collecte a émis le diagnostic natif FAISS Windows `0xc0000008`, mais le code retour pytest est 0. Ce correctif nécessite encore un redémarrage et un test live. Les deux réponses sondes antérieures restent dans le stockage, intactes.

## Défaut d’indexation mémoire utilisateur — correction locale suivante

Après le redémarrage, le tour `d2a1d7e8-37f5-46a0-b8ff-94e70cd17fa9` a encore répondu incorrectement à la question sur la règle Lumina/Flux. La trace montre que le meilleur lot est composé des deux réponses de nos sondes précédentes, lesquelles décrivaient à tort un rôle de Flux différent; leurs références se résolvent aux enregistrements SQLite 8698 et 8699. Une lecture SQLite en mode lecture seule n’a trouvé aucun souvenir indexé contenant la décision utilisateur historique « Lumina cerveau principal, Flux cerveau secondaire/enfant, flux Lumina → Flux ». La réponse incorrecte a depuis été ajoutée comme enregistrement 8700 par le cycle normal de mémoire; aucune entrée n’a été effacée ni réécrite.

La cause suivante est dans l’ingestion/indexation, pas dans un manque de consigne au LLM : `EnhancedAISystem._post_response_processing()` stockait un seul document combinant le message brut de l’utilisateur et jusqu’à 300 caractères de réponse générée; l’embedder indexait ce bloc mêlé. Une longue réponse erronée pouvait donc tirer la représentation vectorielle loin du message source et devenir ensuite un candidat plus convaincant que la déclaration utilisateur. La précédente séparation des rôles dans le texte prompt n’enlevait pas ce biais de l’index.

Correction locale : conserver l’enregistrement épisodique combiné pour le contexte historique et ajouter une entrée `user_message` séparée, limitée à 1200 caractères, dont l’embedding FAISS et le classement lexical utilisent les mots de l’utilisateur sans le préfixe de stockage. Le formateur l’injecte sous une provenance explicite `USER MESSAGE`; la question n’est toujours pas traitée comme preuve de sa réponse. Le reçu de trace identifie ce candidat comme message utilisateur sans révéler son contenu. Les anciennes lignes restent compatibles et inchangées. Cette modification corrige l’indexation des nouveaux tours; elle ne peut pas recréer automatiquement la décision historique absente du stockage existant.

Le chemin profil a aussi été relu : le prompt récupère le profil nommé avec `UserManager.prompt_context_for(user_id)` avant génération; l’apprentissage explicite `learn_from_message()` se déroule après la réponse sur les tours humains uniquement, puis le profil est sauvegardé et invalide son cache en cas de changement. Le profil comportemental `WorldModel.update_from_interaction()` est distinct et résume des thèmes/style, pas des faits explicites. Les reçus de profil et le test live antérieur (« Fred ») confirment la lecture du profil; cela ne prouve pas encore qu’une préférence nouvellement apprise est persistée puis réinjectée au tour suivant. Ce test causal reste à faire après le prochain redémarrage.

Tests locaux après la correction d’indexation : `tests/test_cognitive_log_regressions.py` — **26 passed, 4 subtests**; avertissements Pydantic/pkg_resources/starlette connus; `git diff --check` est propre. **État live non validé** : Lumina a redémarré avant cette modification et doit être redémarrée à nouveau pour charger la nouvelle ingestion. Après redémarrage, valider d’abord un message utilisateur explicite contenant une décision suivie d’une question de rappel paraphrasée; exiger que la trace retrouve le candidat `user_message` pertinent et que la réponse restitue seulement le contenu étayé. Valider ensuite une préférence profil nouvellement déclarée, son reçu `updated`, puis son injection au tour suivant.

## Prise de parole spontanée et avertissement de tokens — vérification après redémarrage

Les logs `[SILENCE] ... engage` et `[utterance — no GUI]` correspondent bien à `PresenceEngine`, pas à une réponse du tour de chat. Dans le code, `core/interface_api.py` transmet le texte brut utilisateur via `notify_user_interaction(topic=text)`. `PresenceEngine` le réinjectait comme « last thing you discussed » tant qu’il avait moins de 9 minutes, même pour les événements `DWELL`/`SILENCE`; en plus, il injectait les questions CAG/ARE sans âge/provenance et leur ajoutait 0,10 de pression. Cela explique comment une ancienne question sur l’identité de la caméra pouvait réapparaître après plusieurs minutes, sous la forme d’une réponse directe adressée à Fred. La cause précise est prouvée dans le code; la ligne de console seule ne permet pas d’attribuer avec certitude le texte exact à `last_topic` plutôt qu’à une question CAG, car le prompt de cette émission n’est pas tracé.

Correction locale : le contexte de message antérieur n’est désormais fourni qu’au mode explicite `resume`, avec une étiquette « contexte historique, pas une nouvelle demande » et une limite d’âge alignée sur la reprise. Les événements ambiants `DWELL`/`SILENCE` ne reçoivent plus les questions/topics CAG sans horodatage, et ces questions ne peuvent plus déclencher à elles seules la pression de parole. Un test couvre l’absence de contexte lors d’un `engage` ambiant et sa présence bornée en mode `resume`. Tests ciblés `tests/test_presence_identity_language.py` : **8 passés**; `py_compile` et `git diff --check` réussis. Ce correctif exige un redémarrage avant validation live.

L’état live après le redémarrage montre `ready=true`; l’événement `Proactive presence utterance` a un `turn_id=null` et est aussi inscrit dans `presence_messages`. En mode sans interface, la callback bulle n’est pas enregistrée par `pages/main_page.py`, donc le TTS reçoit le texte et le fallback le journalise sous `utterance — no GUI`. Le journal confirme l’exécution de la voie de présence, mais pas que son texte soit sémantiquement approprié.

Pour les lignes LM Studio de 17:18:39/43 : le code fournisseur a enregistré `finish_reason=length` et zéro token de contenu visible (`messages=8`). Le pont de chat tente alors `recover_final_response`; ensuite, il journalise que la limite de tokens a été atteinte, y compris si le texte récupéré est conservé. Les deux lignes sont compatibles avec ce chemin, mais elles ne contiennent aucun `turn_id`; sans la trace de ce tour (`final_answer_recovery` et texte final visible), le succès exact de la récupération reste non prouvé. L’état courant ne conserve que le tour Flux plus récent, donc je ne peux pas attribuer rétroactivement ces avertissements à un tour précis.

### Attribution des limites de génération

La revue des avertissements LM Studio montre un flux fournisseur terminé par `finish_reason=length` sans texte utilisateur visible, puis un chemin de récupération finale dans `PersonaBridge`. Le warning précédent disait seulement que le texte visible avait été conservé; il ne distinguait ni une récupération réussie, ni un fallback, ni le tour concerné.

Correction : l'identifiant du tour est transmis comme métadonnée locale au fournisseur (non envoyée au serveur LLM), et les deux journaux indiquent désormais `turn_id`. Le warning du pont donne aussi l'état `final_answer_recovery` et le nombre de caractères visibles. Aucun budget de tokens n'a été augmenté. Cela rend le prochain incident attribuable; les deux lignes historiques du 11 novembre ne peuvent pas être reliées rétroactivement à un tour sans trace conservée.

Vérification après cette correction : `py_compile` sur `cognition/persona_bridge.py` et `managers/llm_manager.py`; suites mémoire, présence et fin de flux — **37 passés, 4 sous-tests passés**. Avertissements de dépendances Pydantic/pkg_resources/starlette présents. Lumina doit être redémarrée pour charger cette attribution; après le redémarrage, vérifier qu'un tour normal puis un tour atteignant la limite produisent les journaux liés au même `turn_id` et que la trace indique le résultat de récupération.

## Audit live après redémarrage — routage interne et identité du profil

Le Brain local est prêt (`http://127.0.0.1:8765/status`, modèle Gemma; le tableau de bord répond sur `8080`). Un tour de chat d’audit a été exécuté via `/chat`; identifiant vérifié dans la trace : `lumina-1794417503193898200-1`.

**Échec observé, avec preuve de tour :** `external_research=results_injected`, `primary_generation=completed`, et la réponse a affirmé l’existence d’un « filtre d’ancrage contextuel » absent du code. Les cinq sources Bing reçues étaient des définitions du mot français « pour », sans rapport avec la question. Le tour n’était pas classé comme question interne, donc le mode `auto` a demandé au petit juge LLM s’il fallait chercher; son verdict a déclenché la recherche. La `pipeline_integrity=consistent` observée ne vérifie que l’ordre/la présence des étapes; elle ne valide pas la réponse sémantique. Ce tour montre précisément pourquoi le manifeste d’exécution seul ne suffit pas.

**Cause de la réflexion caméra antérieure :** la revue du code a établi qu’avant la correction, `PresenceEngine` pouvait présenter `last_topic` comme sujet actuel lors de `DWELL`/`SILENCE`, sans validation de fraîcheur/provenance suffisante. La correction a été commitée (`7625b17`). Ce tour de chat n’a pas reproduit cette émission ambiante; l’état interface courant avait `presence_messages=[]`. Cela ne suffit pas encore à valider le comportement spontané après redémarrage.

**Identité/mémoire :** le même tour a utilisé `user_id=default`; la trace indique `user_profile_context=empty`, `source=no_named_profile`, alors que le magasin de profils persistant indique `active_id=fred`. La récupération mémoire a bien exécuté 6 candidats dans le scope `default`. Le profile learning a terminé, mais aucune preuve de mise à jour/réinjection du profil de Fred n’est fournie par ce tour. Correction préparée : l’API BrainOnly résout uniquement le sentinel `default` vers l’utilisateur actif enregistré; les identités explicitement fournies restent inchangées. Tests couvrent le resolver et son branchement aux deux chemins `/chat` (stream et non-stream).

Le statut `long_horizon_interaction_outcome=skipped_unmatched_turn` est intentionnel : le code refuse de faire avancer un plan social sans corrélation entre sa question et ce tour. Il ne faut pas le requalifier en échec de module; il reste un effet non réalisé faute d’identifiant lié au plan.

**Corrections locales non encore chargées par le processus** : routage des questions causales sur le fonctionnement interne en mode fermé (pas de recherche Web, manifeste de ticks fourni, règle explicite de ne pas inventer la cause d’une réponse sans preuve liée) et résolution du profil `default` vers le profil actif pour l’API BrainOnly.

**Vérification locale :** `py_compile` réussi sur les quatre fichiers touchés; suites ciblées self-description, profil API, présence et logs cognitifs — **53 passés, 4 sous-tests passés**. Les avertissements Pydantic/pkg_resources/starlette restent liés aux dépendances. Un diagnostic natif intermittent `Windows fatal exception 0xc0000008` apparaît parfois pendant l’import FAISS dans les tests cognitifs; malgré ce message, Pytest termine avec le compte de succès ci-dessus. Il faut le suivre séparément et vérifier si le processus Python sort réellement en erreur.

### Reçus causaux de la parole spontanée

Le correctif anti-contexte périmé ne suffisait pas à prouver une décision de présence : les messages UI avaient un identifiant indépendant, mais pas de lien vers le déclencheur ou la voie de génération. Ajout local d’un reçu borné (`presence_id`) pour chaque décision de présence : déclencheur caméra, type d’événement, décision/silence, pression, raison catégorielle, présence/absence des sources de contexte, âge du fil historique, empreinte SHA-256 et longueur de l’énoncé, statut de livraison. Le texte du prompt et l’énoncé brut ne sont pas dupliqués dans ce reçu. L’identifiant est propagé à l’événement UI et au TTS; `/api/interface/status` expose les 40 derniers reçus expurgés.

Vérification locale après ce lot : `py_compile` sur `presence_engine.py`, `state.py`, `interface_api.py`; tests présence, self-description, identité API et régressions cognitives — **56 passés, 4 sous-tests passés**. La suite complète `tests/test_interface_api.py` passe également : **13 tests réussis**, après l’avoir relancée avec l’autorisation locale nécessaire à `asyncio` sous Windows. Total des deux lots : **69 tests et 4 sous-tests réussis**. `git diff --check` est propre. Le blocage initial venait du sandbox qui empêchait les sockets locaux utilisés par `IsolatedAsyncioTestCase`; ce n’était pas un échec applicatif. L’endpoint HTTP `/api/interface/status` et la trace de présence sont couverts par cette suite.

À redémarrer une seule fois après regroupement des prochains correctifs : vérifier dans `/api/interface/status` que `presence_messages[n].presence_id` correspond à `presence_trace[n].presence_id`, que le reçu note `historical_user_message_injected=false` pour `DWELL/SILENCE`, et que ces tours n’interrompent pas un chat actif.

### Portée de la preuve de sortie et réponses tronquées

La trace live précédente avait `pipeline_integrity=consistent` alors que la réponse inventait un mécanisme absent du code et s’appuyait sur des résultats Web hors sujet. La revue confirme que ce statut vérifie l’ordre, les étapes requises et les empreintes de consommation; `output_safety=passed` contrôle la sécurité, pas la vérité. Avant ce correctif, le nom du statut pouvait donc être compris comme une validation cognitive qu’il ne fournit pas.

Correction locale : la trace expose maintenant `pipeline_integrity.scope=execution_order_and_data_flow_only` et `semantic_correctness=not_assessed`. Elle expose séparément `semantic_answer_validation`, soit `not_performed`, soit `scoped_check_performed` uniquement pour le contrôle existant des affirmations d’architecture contre la trace courante. Une fin LM Studio `finish_reason=length` crée le reçu `provider_completion=truncated_by_token_limit` et rend l’intégrité du tour `incomplete_evidence`; le texte partiel reste conservé et son achèvement automatique n’est pas revendiqué. Cela corrige la preuve et le statut; un vérificateur général de factualité n’est toujours pas implémenté et reste une lacune fonctionnelle.

Vérification locale : `tests/test_turn_execution_evidence.py` + `tests/test_self_description_prompt.py` — **25 passed**; `tests/test_interface_api.py` — **13 passed** avec accès loopback autorisé. Les essais combinés ont d’abord rencontré le blocage sandbox de sockets asyncio; relancées séparément, les deux suites passent. Les avertissements sont ceux de dépendances (Pydantic/pkg_resources/Starlette). Aucun redémarrage Lumina n’est demandé avant le lot de validation live regroupé.

### Mémoire et profil utilisateur — preuve de transmission aval

La lecture du flux confirme que le compteur de mémoire récupérée seul ne prouve pas qu’un souvenir a atteint le LLM. Le prompt ne prend que 5 éléments (8 si le tour est marqué surprenant) parmi les candidats récupérés; la trace ne distinguait pas auparavant les candidats rappelés de ceux réellement injectés. Ajout local d’un reçu expurgé `memory_prompt_context` avec références hachées et type/niveau de chaque souvenir effectivement formaté. Le reçu consomme `memory_retrieval`; `prompt_assembly` consomme maintenant ce reçu ainsi que le reçu de profil. Cela prouve la chaîne rappel → sélection pour prompt → assemblage, sans prétendre que le modèle a effectivement utilisé le contenu dans sa réponse.

Le profil a lui aussi été suivi de bout en bout : une déclaration explicite acceptée produit un reçu `updated`, est écrite dans `users.json`, survit au rechargement du gestionnaire, puis apparaît dans le contexte de prompt du tour suivant sous le même utilisateur résolu. Le test ajouté valide précisément cette persistance; les déclarations ambiguës ou transitoires restent rejetées/quarantinées par les règles existantes.

Vérification : `tests/test_cognitive_log_regressions.py`, `tests/test_brain_default_user_resolution.py` et `tests/test_turn_execution_evidence.py` — **42 passed, 4 sous-tests passés**; avertissements de dépendances seulement. Lacune restante : aucune preuve ne peut établir l’attention interne du LLM à un souvenir injecté; on peut prouver son inclusion et les effets de profil, pas la causalité sémantique sans une évaluation de réponse dédiée.

## Boucle cognitive interne — reçus de cycle causaux

Le focus de l’audit est maintenant le moteur cognitif de fond. Les compteurs agrégés de `ModuleTickLog` prouvent qu’un module a été appelé à un moment donné, mais ils ne disent pas quels composants ont participé au même cycle, quelle sortie a été consommée en aval, ni si le cycle a échoué. La revue de `core/internal_loop.py` confirme le chemin central : Phase 1 compétition → arbitrage exécutif → commit/read-back du but sélectionné → publication du gagnant; et TTE → CDE → DTS → publication de la pensée dominante. GoalEngine et GoalActionExecutor tournent dans le cycle selon leurs gates/cadences.

Correction locale : chaque slow cycle garde maintenant un reçu borné (40 en mémoire, 5 exposés par défaut dans le statut Brain). Il identifie le cycle, sa durée et son issue, les étapes sélectionnées, leurs statuts et des empreintes d’entrée/sortie. Les liens de consommation sont explicites aux frontières instrumentées : compétition→arbitrage→publication, TTE→CDE→DTS→pensée publiée, GoalEngine→broadcast, et gagnant récent→GoalActionExecutor. Les appels interceptés de `ModuleTickLog` sont automatiquement attachés au reçu du thread de cycle; une tâche simultanée du chat ne peut pas se faire attribuer au cycle de fond. Les raisons de cadence/gouverneur, sorties absentes, erreurs de ces chemins et cycles échoués sont distingués. Le reçu ne conserve ni texte de pensée, ni texte utilisateur, ni détails personnels; seuls des résumés de forme/compteurs et des empreintes sont exposés. `core/state.py` inclut ce reçu dans `brain_workflow_status`.

La portée est volontairement limitée : une empreinte consommée démontre le passage d’une valeur structurée entre ces étapes, pas la qualité de la décision ou une compréhension sémantique. Tous les appels interceptés par `ModuleTickLog` sont également inclus comme étapes de cycle, avec durée et sortie résumée; cependant, les liens consommateur/producteur explicites ne sont pas encore présents pour chaque paire de modules. Le GoalEngine lit son état interne de pression/sémantique; aucun lien artificiel vers le gagnant de Phase 1 n’est revendiqué. Un résultat `completed` signifie que le cycle d’orchestration est revenu sans exception non interceptée, pas que chaque sous-module a réussi ni que sa sortie est bonne. Pour garder le statut borné, chaque reçu retient au plus 256 étapes, avec un compteur de débordement.

Tests ajoutés : cinq cas vérifient les références de consommation, la preuve d’un tick réel dans un reçu par cycle, l’absence de texte privé, la rétention bornée, l’enregistrement d’un cycle échoué/en cours et l’absence d’attribution d’un appel concurrent au cycle actif. Vérification locale du lot : **32 tests passés et 3 sous-tests passés** dans les suites cycle, ticks, workflow et ordre du pipeline; compilation Python réussie. Avertissements Pydantic/pkg_resources/Starlette préexistants. Le code est local; le processus Lumina actuel ne peut pas l’exécuter avant le prochain redémarrage. Après validation groupée, appeler `/status` et examiner `components.internal_thought_loop.cycle_evidence` sur plusieurs cycles : vérifier que les étapes apparaissent selon leurs cadences, que les références des consommateurs correspondent aux producteurs et que les échecs sont visibles. Le verdict sur la qualité cognitive de la boucle reste ouvert et nécessitera ensuite des scénarios d’entrée représentatifs, un effet interne attendu et la vérification de l’état aval correspondant.

### Contrat d’échec du GoalEngine

Une seconde lecture de l’étape GoalEngine a révélé un défaut d’orchestration réel : `GoalEngine.tick()` capture ses propres exceptions et retourne normalement. L’observateur externe voyait alors un appel achevé avec sortie `None`, indistinguable d’un succès ou du cooldown; le loop pouvait ensuite republier les pensées de buts persistées avant l’échec. Le module expose maintenant un reçu minimal `completed` / `skipped_cooldown` / `failed`, avec compteurs et type d’erreur seulement. Le slow cycle consomme ce reçu; en cas d’échec, il marque l’étape et saute le broadcast de pensées anciennes. Le comportement normal et le cooldown gardent leur publication.

Vérifications après cette correction : la suite regroupée (GoalEngine, cycle causal, exécuteur, publication, workflow, ticks et ordre de sélection) passe **40 tests et 3 sous-tests**, compilation et `git diff --check` réussis. Le résumé de cycle expose une liste blanche de compteurs utiles (buts, candidats, threads, broadcasts, scores) tout en excluant les champs textuels libres. Le défaut d’observabilité et le risque de republication après exception sont corrigés localement; il reste à vérifier les états de tick et les broadcasts avec le reçu live après un unique redémarrage groupé. Le prochain axe est la provenance des pensées converties en propositions, puis l’évaluation d’effets internes sur des scénarios représentatifs; je ne conclurai pas sur la qualité cognitive à partir de ces seuls reçus.

### Sujet et provenance des objectifs issus des pensées

La revue du chemin Phase 1 → proposition → persistance a mis au jour une perte de structure : `Thought` peut déjà porter un `topic`, mais `SimpleThoughtEvaluator` dérivait toujours le sujet depuis le début du texte généré. Cela rendait possible qu’une prose réflexive fournisse le sujet d’un objectif au lieu du concept structuré produit en amont. Le chemin de proposition ne conservait ensuite que l’identifiant de pensée, ce qui empêchait d’auditer sa source, son type et son horodatage après lecture depuis le registre des buts.

Correction : l’évaluateur privilégie maintenant `topic`/`concept` lorsqu’ils existent et garde l’extraction textuelle uniquement pour les pensées historiques non structurées. La méthode choisie est explicitement marquée (`structured_topic` ou `legacy_text_extraction`). Source, type et horodatage de la pensée sont transportés avec la proposition et persistés dans le but; le commit relit le registre et vérifie ces champs avant de déclarer la création vérifiée. Les doublons conservent également les références des pensées de soutien. Le reçu du cycle expose la source/type/méthode sans exposer le contenu textuel. Autre correction de comptabilité : `accepted_candidate_count` ne compte désormais que les admissions dont `add_goal()` confirme le succès, au lieu de compter un objectif déjà présent comme nouvellement accepté.

Vérification locale de ce lot : compilation Python réussie; suites proposition pensée→but, rapport GoalEngine, régressions cognitives, ordre GoalEngine et reçu de cycle — **45 tests passés, 4 sous-tests passés**; `git diff --check` propre. Avertissements uniquement de dépendances déjà connues. Cela corrige la traçabilité et l’exactitude du compteur; cela ne prouve pas encore que les sujets retenus sont cognitivement pertinents. Prochaine étape de l’audit : cartographier les différents écrivains de buts (proposition sélectionnée, génération autonome du GoalEngine, GoalQualityFilter, MotivationalField), établir les contrats voulus entre eux, puis vérifier par scénario si leurs sorties entrent dans le bon arbitre et ont des effets aval cohérents. La validation live de ce lot attendra le redémarrage groupé déjà prévu.

### Besoins internes asynchrones — résultat rattaché au cycle d’origine

La vérification du chemin MotivationalField a révélé que `tick()` lançait un thread daemon pour scanner les besoins puis retournait immédiatement. Le tick paraissait donc terminé avant le résultat; le thread pouvait créer des buts sans preuve de fin dans le cycle et un scan lent pouvait chevaucher le suivant. Le compteur de ticks ne distinguait pas « travail planifié » de « scan terminé ».

Correction locale : `tick()` renvoie maintenant un statut explicite de mise à jour des drives et du scan (`scheduled`, `skipped_overlap`, `not_due`). Le worker conserve un état borné (`running/completed/failed`, cycle, nombres de besoins/actions, durée et type d’erreur), empêche le chevauchement et ajoute un reçu asynchrone au reçu du cycle d’origine, même si celui-ci est déjà terminé. Il ne peut pas écrire sur le cycle devenu courant entre-temps. Le résultat du scan compte les besoins détectés et les actions effectivement acceptées par leurs consommateurs; les cibles et descriptions personnelles ne sont pas copiées dans le reçu.

Vérification locale : compilation réussie; tests MotivationalField, reçus de cycle (dont worker asynchrone sur le bon cycle), rapport GoalEngine et proposition sélectionnée — **20 tests passés**; `git diff --check` propre. Le lot précédent de provenance pensée→but est déjà sur GitHub (`3de6229`); ce correctif asynchrone est encore local et attend commit/push. Limite restante : les autres chemins d’écriture GoalQualityFilter et GoalEngine doivent être comparés et tracés jusqu’à leurs lectures aval; aucun résultat live de ce code n’est revendiqué avant le redémarrage groupé.

### Writers de buts — admission unique et conservation des enregistrements

La cartographie a confirmé une incohérence de persistance, pas seulement une différence de style : le GoalQualityFilter écrivait les remplacements directement via DataAccess, tandis que `GoalEngine.add_goal()` remplaçait ensuite le fichier entier à partir de son seul registre mémoire. Les objectifs `low_quality` et des champs DAL (score qualité, raisons, historique de réparation) absents du registre actif pouvaient ainsi disparaître; un registre GoalEngine périmé pouvait aussi rétablir un objectif marqué comme bruit. De plus, le filtre créait des objectifs sans passer par les contrôles d’admission du moteur.

Correction locale : les objectifs générés par GQF passent maintenant par `GoalEngine.add_goal()`; après l’évaluation et ses écritures DAL, le moteur recharge le registre avant d’admettre les remplacements. Les écritures GoalEngine fusionnent leurs champs autoritatifs avec les champs complémentaires déjà présents, préservent les enregistrements absents du pool actif, et ne retirent ces archives que lors d’un recyclage explicite. Le recyclage intervient après les contrôles de refus/doublon et restaure la victime si la sauvegarde échoue. Dans la boucle, le GQF est sauté avec un état explicite si le scan MotivationalField est encore en cours, évitant que les deux writers modifient simultanément le registre.

Vérification locale : compilation réussie; suites GoalEngine persistence, régressions cognitives, tick, reçus de cycle, MotivationalField, ordre et proposition sélectionnée — **52 tests passés et 4 sous-tests passés**; `git diff --check` propre. Tests couvrent la conservation de champs qualité et d’archives pendant l’admission, le recyclage explicite, le refus d’un doublon sans éviction et le passage GQF → GoalEngine. Le lot est encore local. La suite de l’audit porte sur les autres producteurs (autonomous curiosity, thought-goal linker, completion/consolidator), leurs contrats d’admission, et les effets consommés en aval; aucune prétention de validation live n’est faite avant le redémarrage groupé.

### Phase 2 et consolidateur — mutations synchronisées avec le moteur actif

La lecture du chemin V33 a confirmé que `ThoughtGoalLinker` créait lui aussi des objectifs directement par DataAccess. Il pouvait donc contourner les mêmes contrôles et laisser l’exécuteur lire un registre mémoire obsolète après une mise à jour ou une fusion. Son chemin de création utilise maintenant `GoalEngine.add_goal()`, conserve l’identifiant et le type de la pensée source, et Phase 2 resynchronise le registre après mutations. Le consolidateur continue d’écrire ses fusions/archives par DataAccess, mais la boucle recharge le GoalEngine lorsque son rapport signale une modification, avant les consommateurs suivants.

Vérification locale : compilation réussie; tests du linker Phase 2, orchestrateur, persistance GoalEngine, reçus de cycle, MotivationalField et régressions — **44 tests passés et 4 sous-tests passés**; avertissements de dépendances seulement. Le lot est local et attend le commit/push. La voie de mise à jour/fusion historique du linker utilise encore DataAccess, mais son effet est suivi par rechargement; les créateurs actifs connus (Phase 1, GoalEngine autonome, GQF, MotivationalField, Phase 2) passent maintenant l’admission centrale ou sont synchronisés avant consommation. Prochaine vérification : lifecycle/completion et tests d’ordre d’effets, puis audit des sorties internes représentatives.

### Completion — aucun succès narratif sans écriture confirmée

Le chemin partagé `record_goal_completion()` ignorait la valeur booléenne de `GoalEngine.complete_goal()` et de `DataAccess.save_goal()`: un refus ou un échec de sauvegarde était traité comme une réussite, puis un chapitre de récit de vie pouvait être enregistré et le log annoncer « GOAL COMPLETED ». Cette sortie interne pouvait donc affirmer un effet non réalisé.

Correction locale : la complétion ne retourne `True` et ne déclenche le chapitre narratif que si un store retourne explicitement `True`. En l’absence de confirmation, le chemin retourne `False`, n’ajoute aucun récit, et journalise le refus de persistance. Les tests couvrent refus moteur, échec DAL et succès moteur.

Vérification locale : compilation réussie; complétion, deadlock, persistance, admission Phase 2, cycle et régressions cognitives — **42 tests passés et 4 sous-tests passés**; `git diff --check` propre. Le correctif est local et attend le prochain commit/push. Cela ferme une incohérence d’effet aval vérifiable; il reste à tester les transitions de cycle complet, notamment si l’état complété est consommé ensuite par l’économie, le Workspace et le prochain tick sans réapparition d’un but obsolète.

Vérification aval complémentaire : `GoalEngine.update_goals()` et `GoalActionExecutor` ignoraient également le retour de `record_goal_completion()` et pouvaient donc journaliser un but terminé après un échec de persistance. Le filtre GQF comptabilisait de même un but comme « settled » sans confirmation. Ces trois consommateurs exigent maintenant le succès confirmé; l’engine continue son lifecycle normal si la complétion échoue, et GQF rapporte séparément les écritures manquées. Tests lifecycle/refus et régressions — **44 passés et 4 sous-tests passés**. Ces changements restent locaux et seront commités avec leur groupe de tests.

### MotivationalField — scans parallèles et durabilité de l’état

Le scan des besoins et l’intégration des drives pouvaient appeler `_save()` depuis des threads différents. L’écriture précédente tronquait directement le JSON sans verrou d’écriture ni remplacement atomique; un chevauchement pouvait corrompre le fichier. En outre, le tick rapportait seulement une tentative même si l’intégration ou la sauvegarde échouait.

Correction locale : les sauvegardes sont maintenant sérialisées, écrites dans un fichier temporaire, remplacées atomiquement et relues pour confirmer les champs principaux. `_save()` retourne un booléen réel. Les sorties de tick/scan distinguent `completed`, `persistence_failed` et `failed`, avec compteurs bornés; le statut expose le dernier état de scan. Un test concurrent vérifie que les écritures répétées restent JSON valides et ne laissent pas de temporaire.

Vérification locale : **45 tests passés et 4 sous-tests passés** (MotivationalField, reçu asynchrone, complétion, persistance objectifs et régressions), compilation réussie, `git diff --check` propre. Ce lot est local et attend commit/push. Les cycles de drive et de besoins ont maintenant un statut d’exécution/durabilité testable; reste à valider un cycle complet à l’exécution live après le redémarrage groupé.

### Parcours pensée structurée → workspace — preuve aval ajoutée

Un test de parcours couvre maintenant les composants réels jusqu’au consommateur suivant : `Thought.to_dict()` → `DataAccess.add_thought/get_thoughts` (normalisation du schéma) → `SimpleThoughtEvaluator.evaluate_recent_thoughts()` → candidat `WorkspaceCompetition` → proposition retenue → `GoalEngine.commit_selected_thought_proposal()` avec relecture vérifiée du registre → `GoalEngine.get_goal_thoughts()`.

Résultat observé : `topic`, identifiant, source et type de la pensée restent cohérents; le sujet structuré (`cognitive_execution_flow`) est utilisé plutôt qu’une extraction du texte; le candidat retenu conserve la proposition source; le but persisté ressort comme candidat actif consommable par le workspace. Le test ne prouve pas que le modèle choisit toujours un sujet pertinent : il prouve le contrat de données et les effets aval sur ce chemin lorsqu’une proposition est retenue.

Vérification locale après ajout : `tests/test_selected_thought_goal_pipeline.py` + `tests/test_cognitive_log_regressions.py` — **34 tests passés, 4 sous-tests passés**; `git diff --check` propre. Avertissements connus de Pydantic, `pkg_resources` et `python_multipart` uniquement.

**Mise à jour de statut :** les mentions plus anciennes de sections précédentes disant que les correctifs GoalEngine, Phase 2, completion ou MotivationalField « attendent commit/push » sont historiques et dépassées. Les lots de code ont été poussés sur `main` jusqu’à `d430e05`; ce nouveau test et la présente preuve sont le lot suivant. Le worktree contient par ailleurs d’autres modifications utilisateur non liées; elles ne font pas partie de l’audit et ne sont pas incluses.

**Suite de l’audit du cœur :** le parcours confirme le flux retenu mais pas encore la qualité des décisions en situation de concurrence, ni les effets du GoalEngine autonome sur plusieurs cycles. Étape suivante : scénarios de replay déterministes sur entrées contradictoires/bruitées, avec vérification du gagnant, de la proposition retenue, des buts créés ou rejetés, du broadcast et du cycle suivant. La validation live demeure groupée après redémarrage.

### Broadcast vers le workspace — reçu fondé sur l’admission réelle

L’inspection du producteur de reçus a révélé un faux positif concret : le code incrémentait `broadcast_count` après l’appel à `GlobalWorkspace.broadcast()` sans examiner son booléen. Or l’API retourne `False` quand son filtre sémantique bloque un élément. Le cycle pouvait donc marquer un broadcast comme réussi alors que le workspace ne l’avait pas accepté.

Correction : le broadcast des pensées du GoalEngine compte maintenant uniquement les retours `True`. Les reçus distinguent `completed`, `partial`, `rejected` et `failed`, avec demandes, admissions, refus et exceptions séparés. Les erreurs individuelles ne sont plus avalées comme si elles représentaient une admission.

Tests ajoutés : admission/refus/exception mixte et refus total sans fausse réussite. Vérification locale : boucle, parcours pensée→workspace et régressions cognitives — **43 tests passés, 4 sous-tests passés**; `git diff --check` propre. Les avertissements de dépendances restent sans lien avec ce correctif.

Portée : cela rend la preuve d’effet workspace honnête. La prochaine vérification doit encore suivre ce qui lit effectivement ces éléments après admission et comparer le gagnant du cycle au contexte consommé par le tour de chat; un broadcast accepté ne prouve pas à lui seul qu’il a influencé la réponse.

### Contexte cognitif du tour → prompt reçu par le modèle

La trace du tour marquait la construction du contexte cognitif comme `completed`, mais sans empreinte de sortie et sans lien de consommation dans `prompt_assembly`. Un tick du harnais pouvait donc apparaître à côté d’une réponse sans preuve que son contexte avait été inséré dans le prompt effectivement préparé.

Correction : le constructeur reçoit le `turn_id` capturé avant son exécution dans le worker; la sortie du contexte cognitif est enregistrée sous forme d’empreinte et résumé redigé sur ce tour précis. `prompt_assembly` référence explicitement cette empreinte comme entrée, et `generation_request` reste lié à l’assemblage. La trace ne conserve pas le texte privé du contexte.

Vérification locale : tests de trace de tour, parcours pensée→workspace et reçus internes — **28 tests passés**, compilation de `persona_bridge.py` et `internal_loop.py` réussie, `git diff --check` propre. Le groupe intégré antérieur (11 suites sur boucle, propositions, GoalEngine, completion, MotivationalField et Phase 2) reste vert : **65 tests passés, 4 sous-tests passés**.

Limite : la liaison prouve que le bloc cognitif construit est consommé par l’assemblage du prompt préparé. Elle ne prouve ni que le LLM a suivi ce contexte, ni la qualité sémantique de sa réponse. Ces éléments exigent les scénarios live et l’évaluation des sorties.
