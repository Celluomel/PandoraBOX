# Lumina Embodied World Model (Body)

> **Statut : IMPLEMENTÉ & VÉRIFIÉ** — 144 tests + 36 subtests verts, tâche simulée
> résolue de façon reproductible (433 / 583 / 798 pas sur 3 runs), erreur de
> prédiction en décroissance (EMA 0.28 → 0.18 → 0.08).
>
> Le Body est **séparé** du Brain. Cette doc ne concerne que le côté Body
> (`body_runtime_host/`) et sa façade distante lue par le Brain (read-only).

---

## 1. Principes implémentés

Les 7 principes d'un world model, incarnés :

| Principe | Implémentation |
|---|---|
| **Représentation** | Latent physique `s_t` = encodeur du cortex (features sensorimoteurs 412-dim : sémantique 384 + géométrie analytique 20 + corps 8) projeté sur 32-dim (`dynamics.py`) |
| **Dynamiques** | `LatentWorldDynamics` : transition latente action-conditionnée `s_{t+1} = f_dyn(s_t, a_t)` (torch MLP, repli numpy si torch absent) |
| **Imagination** | `Policy.evaluate()` : rollout latente sur horizon 8, contrefactuels depuis le même état (effet causal isolé) |
| **Contrefactuel** | `dynamics.counterfactual(s, a, h)` : chaque candidate action évaluée depuis l'état identique |
| **Causalité** | Dynamique *action-conditionnée* + contrefactuels ; la politique choisit l'action au meilleur futur simulé, pas la meilleure récompense immédiate |
| **Stabilité long-horizon** | Latent borné (tanh), erreur de prédiction RMS scale-free, consolidation périodique, ancres avec fiabilité bornée |
| **Planification** | `Policy.decide()` : sélection par valeur imaginée (value head TD-bottstrap + BCE succès) — *décision guidée par anticipation* |

**Principes sous-jacents** (spécification incarnée) :
- **Le "cortex visuel" est un encodeur d'affordances, pas un décodeur** :
  `ArtificialCortex` produit which2act / where2act / how2act conditionnés par
  l'état du corps (reach, strength, gripper) — pas une scène neutre.
- **Vision = encoder ce qui est actionnable** : géométrie *relative au corps*
  (distances, bearings, atteignabilité, **distances par type d'objet**).
- **Apprentissage continu** : pas de fin de training — chaque pas alimente
  replay-buffer, TD-update, révision d'ancres, consolidation.
- **Stabilité/plasticité** : ancres fiables mises à jour lentement, récentes
  rapidement ; exploration qui s'annule (0.40 → 0.08) avec l'expérience.
- **Révision des connaissances** : chaque expérience nouvelle teste les
  modèles internes (prédiction vs réalité → erreur → correction ciblée).

---

## 2. Architecture

```
                     ┌────────────────────────────────────────────┐
   Brain (read-only) │        BODY RUNTIME HOST  (port 8766)      │
   RemoteWorldModel ─┤  BodyRuntime : /sensors /command /health   │
   (cognition/body_  │  /reset /config /worldmodel/*              │
    runtime/remote)  │                                            │
                     │  ┌──────────────────────────────────────┐  │
                     │  │   EmbodiedWorldModel (worldmodel/)    │  │
                     │  │                                        │  │
   capteurs réels    │  │  sources.py                            │  │
   (robot / HA)      ─┼─▶  RobotSource  (HTTP robot_sim :9100)   │  │
                     │  │  SimRobotSource (sandbox, défaut)      │  │
                     │  │  NullSource (aucun capteur)            │  │
                     │  │                                        │  │
                     │  │  core.py — boucle 11 étapes            │  │
                     │  │   1 observe → 2 body state →           │  │
                     │  │   3 cortex encode (affordances) →      │  │
                     │  │   4 activation ancres →                │  │
                     │  │   5 latent physique →                  │  │
                     │  │   6 latent cognitif (context Brain) →  │  │
                     │  │   7 état global →                      │  │
                     │  │   8 décision (rollout imaginés + prior)│  │
                     │  │   9 exécution (acteurs / sandbox) →    │  │
                     │  │  10 apprentissage (erreur prédictive,  │  │
                     │  │     replay, TD, consolidation) →       │  │
                     │  │  11 log épisode + sauvegarde           │  │
                     │  │                                        │  │
                     │  │  cortex.py — encodeur d'affordances    │  │
                     │  │  anchors.py — lieux/objets/trajectoires│  │
                     │  │  dynamics.py — transition latente      │  │
                     │  │  policy.py — décision par anticipation │  │
                     │  │  consolidation.py — révision/renfo.    │  │
                     │  │  types.py — BodyState/Outcome/Anchors  │  │
                     │  │  sim_world.py — sandbox (tasse→étag.)  │  │
                     │  │  robot_sim.py — robot simulé HTTP      │  │
                     │  └──────────────────────────────────────┘  │
                     └────────────────────────────────────────────┘
```

### Fichiers

| Fichier | Rôle |
|---|---|
| `body_runtime_host/runtime.py` | Serveur HTTP du Body (capteurs, commandes, santé, config, world model) |
| `body_runtime_host/robot_sim.py` | Robot simulé autonome (HTTP : capteurs/commandes) — sandbox "vraie" pour le mode robot |
| `body_runtime_host/worldmodel/core.py` | `EmbodiedWorldModel` — la boucle incarnée (11 étapes), config, reset, consolidation |
| `body_runtime_host/worldmodel/cortex.py` | `ArtificialCortex` — encodeur d'affordances ; géométrie analytique corps-relative ; fallback hash-embedder |
| `body_runtime_host/worldmodel/anchors.py` | Mémoire physique : `AnchorLieu`, `AnchorObjet`, `AnchorTrajectoire` (fiabilité, utilité, upsert, consolidation) |
| `body_runtime_host/worldmodel/dynamics.py` | `LatentWorldDynamics` — encodeur + transition + value head, replay buffer, save/load torch |
| `body_runtime_host/worldmodel/policy.py` | `Policy` — évaluation contrefactuelle des candidats, exploration softmax, prior d'orientation |
| `body_runtime_host/worldmodel/consolidation.py` | `ConsolidationEngine` — révision/renforcement/dépréciation des ancres (stabilité vs plasticité) |
| `body_runtime_host/worldmodel/sources.py` | `NullSource`, `SimRobotSource`, `RobotSource` (HTTP) — même interface observe/body_state/execute |
| `body_runtime_host/worldmodel/sim_world.py` | `SimulatedRoom` — physique sandbox : reach/strength gating, collisions, portage, tâche tasse→étagère |
| `body_runtime_host/worldmodel/types.py` | Types de base sérialisables (BodyState, Observation, Action, Outcome, Episode, GlobalState) |
| `cognition/body_runtime/remote.py` | **Côté Brain (non modifié ici)** : `RemoteWorldModel` — façade distante read-only vers le host |

### Séparation Brain / Body (gardefous)

- Le **Body** possède la connaissance physique du monde (ancres, dynamique,
  politique) — il agit et apprend.
- Le **Brain** n'y accède que par `RemoteWorldModel` (HTTP, read-only) via
  `context_for_brain()` — "preuve physique groundée, pas croyance abstraite".
- Le Brain ne modifie jamais directement le corps ni les ancres ; le Body ne
  modifie jamais la cognition du Brain.

---

## 3. Tâche de référence (sandbox)

**Pièce 12×12** : table (4,4), chaise (8,3), pilier-obstacle (6,6),
**tasse** (10,9, cible), **étagère** (1,9, zone de dépose).

**Tâche** : saisir la tasse, la porter à l'étagère, la poser.

Physique : reach 1.8 (gating grab/push), strength 30 (gating push),
gripper mono-slot (pas de grab en portant), collisions bloquantes (danger),
objet porté suit le corps.

Récompenses :
| Événement | Signal |
|---|---|
| Grab de la tasse | +0.3 |
| Grab d'un autre objet | +0.05 |
| **Dépose sur l'étagère** | **+1.0 (fin de tâche)** |
| Dépose hors étagère | −0.3 (failure) |
| Collision | −0.2 (danger) |
| Shaping continu | −0.02 × distance (tasse si non portée, étagère si portée) |
| Push | **neutre** (0.0) — interaction, pas un succès |
| Grab en portant / grab vide / release vide | −0.05 (failure) |

---

## 4. Mécanismes d'apprentissage (points clés)

1. **Features par type d'objet** (`cortex.py` idx 16–19) : distance
   normalisée vers la cible/la table/la chaise/l'obstacle — la représentation
   *doit* pouvoir lire "combien reste-t-il jusqu'à la tasse", sinon la value
   head ne peut pas apprendre (cause racine de l'échec initial).
2. **Prior d'orientation par affordances** (`core._steering_prior`) : bonus
   faible (≤0.072) sur forward/turn selon le bearing de la cible — signal
   d'exploration **phase-aware** (cible = tasse au départ, **étagère en
   portant**), constant et dominé par la valeur apprise dès qu'elle existe.
3. **Pas d'optimum local de push** : push neutre (avant +0.05 → boucle
   "pousser la table" 2000+ pas).
4. **Gripper mono-slot** : avant, grab en portant *remplaçait* l'objet porté
   (la tasse retombait) — corrigé en failure.
5. **Apprentissage** : Adam lr 5e-3, batch 64, 2 epochs/pas, replay 4096,
   TD-bootstrap γ 0.95 + BCE succès ; consolidation toutes les 50 étapes.
6. **Exploration** : 0.40 → 0.08 (annealing 0.997^steps), softmax température 0.5.

---

## 5. Exécuter

```bash
cd C:\Users\frede2\test\lumina_v110_temp

# Tests (Body + Brain — tout le repo)
venv\Scripts\python.exe -m pytest tests/ -q
# → 144 passed, 36 subtests passed

# Démo d'apprentissage (tasse → étagère)
venv\Scripts\python.exe scripts\body_worldmodel_demo.py --steps 3000 --reset
# → "*** TASK COMPLETE at step N ***" (vérifié : 433 / 583 / 798 pas)

# Host Body (HTTP :8766) + robot simulé (HTTP :9100)
venv\Scripts\python.exe -m body_runtime_host
venv\Scripts\python.exe -m body_runtime_host.robot_sim --host 127.0.0.1 --port 9100

# Config world model (mode sim | robot | bridge)
curl http://127.0.0.1:8766/worldmodel/config
curl -X POST http://127.0.0.1:8766/worldmodel/config -H "Content-Type: application/json" -d "{\"mode\": \"robot\", \"ROBOT_HOST\": \"127.0.0.1\", \"ROBOT_PORT\": 9100}"
```

Côté Brain (déjà en place, **non modifié**) : config `BODY_HOST=127.0.0.1`,
`BODY_PORT=8766` ; `BodyRuntime.worldmodel` résout d'abord le host distant,
fallback local in-process.

---

## 6. Données persistées

`data/body/worldmodel/` :
- `anchors.json` — lieux / objets / trajectoires (fiabilité, utilité, historique)
- `dynamics.pt` — poids encodeur + dynamique + value head (rejeté proprement si
  la dim des features change — ex. GEOM_DIM 16→20)
- `episodes.jsonl` — journal des épisodes (trimmé à 2000)
- `config.json` — config active (écrase les défauts)

---

## 7. Résultats vérifiés (exécution réelle, session du 21/09)

| Run | Pas jusqu'à la fin | PE final (EMA) | Collisions | Ancres |
|---|---|---|---|---|
| 1 | **433** | 0.278 | 9 | 10 lieux, 4 objets, 8 traj |
| 2 | **583** | 0.176 | 32 | 9 lieux, 4 objets, 8 traj |
| 3 | **798** | **0.085** | 87 | 16 lieux, 4 objets, 8 traj |

- Tâche complète : `done=true, successes=1` sur les 3 runs.
- Context Brain final : « Physical task state: complete … Last goal success at
  step N. »
- Ancres consolidées : reliability jusqu'à 1.00, utilité jusqu'à +30 (lieux de
  prise de la tasse) ; « release » passe de utilité −0.09 à **+0.18**.

---

## 8. Pitfalls rencontrés (mémo)

1. **Représentation insuffisante** → la value head ne peut pas apprendre
   « proche de la tasse = bon ». Ajouter des invariants analytiques (distance
   par type) a débloqué l'apprentissage.
2. **Récompense positive sur une interaction neutre** (push +0.05) → optimum
   local « pousser pour toujours ». Les interactions neutres ne doivent pas
   porter de signal positif.
3. **Prior qui s'effondre trop vite** (décroissance exponentielle) → exploration
   aveugle tardive. Un prior faible et constant est préférable : c'est un
   biais d'exploration, pas un contrôleur.
4. **Sémantique d'action incorrecte** (grab qui remplace l'objet porté) →
   comportement « grab-dépose-grab » illimité. La physique doit être fidèle
   (gripper mono-slot).
5. **Anciens poids incompatibles** : `dynamics.pt` garde la `in_dim` ; si les
   features changent, le chargement détecte le mismatch et repart frais — ne
   pas supprimer le check.
