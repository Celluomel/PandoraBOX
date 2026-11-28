"""
Phase 2.2: Thought-Goal Linker

Enables dynamic goal creation and mutation from thoughts.
Goes beyond simple goal creation to support:
- Goal priority updates based on thought urgency
- Linking thoughts to existing goals
- Genealogy tracking (which thoughts led to which goals)
- Goal evolution over time
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class ThoughtGoalLinker:
    """
    Links thoughts to goals dynamically.
    
    Capabilities:
    - Create new goals from thoughts
    - Update priority of existing goals
    - Link thoughts to goals
    - Track genealogy (thought→goal lineage)
    - Merge similar goals
    """
    
    def __init__(self, persona_dir: str = "data/persona", goal_engine=None):
        self.persona_dir = Path(persona_dir)
        self.goal_engine = goal_engine
        
        # Similarity threshold for goal merging
        self.merge_threshold = 0.8
        
        # Priority boost factors
        self.urgency_boost_factor = 0.3
        self.repetition_boost_factor = 0.1
    
    def process_thought_evaluation(self, evaluated_thought: Dict, goal_engine=None) -> Dict:
        """
        Process an evaluated thought and create/update goals.
        
        Args:
            evaluated_thought: Output from AdvancedThoughtEvaluator
        
        Returns:
            Dict with actions taken: created_goals, updated_goals, linked_goals
        """
        result = {
            'created_goals': [],
            'updated_goals': [],
            'linked_goals': [],
            'merged_goals': []
        }

        # Numeric actionability alone is not authority to mutate durable goals.
        # Require the structured signal emitted by AdvancedThoughtEvaluator.
        from cognition.thought_signals import signal_for_thought
        cognitive_signal = signal_for_thought(evaluated_thought)
        if cognitive_signal is None:
            return result
        
        # Load current goals
        goals = self._load_goals()
        engine = goal_engine or self.goal_engine
        if engine is None:
            from cognition.goal_engine import GoalEngine
            engine = GoalEngine(
                None, persistence_file=str(self.persona_dir / "goals.json")
            )
            self.goal_engine = engine
        
        # 1. Check if thought links to existing goal
        linked_goal = self._find_similar_goal(evaluated_thought, goals)
        
        if linked_goal:
            # Update existing goal
            self._update_goal_from_thought(linked_goal, evaluated_thought)
            result['linked_goals'].append(linked_goal['id'])
            result['updated_goals'].append(linked_goal['id'])
        
        # 2. Create new goal if actionable enough
        elif evaluated_thought.get('actionability', 0) > 0.6:
            new_goal = self._create_goal_from_thought(evaluated_thought)
            from cognition.goal_engine import Goal
            engine.reload_from_disk()
            accepted = engine.add_goal(Goal(
                id=str(new_goal['id']),
                topic=str(new_goal.get('description') or new_goal.get('name') or ""),
                origin="thought_goal_linker",
                priority=float(new_goal.get('priority', 0.5)),
                energy=float(new_goal.get('priority', 0.5)),
                created_cycle=int(getattr(engine, "_cycle_counter", 0)),
                last_active=int(getattr(engine, "_cycle_counter", 0)),
                source_thought_id=str(evaluated_thought.get('origin_thought_id') or ""),
                source_thought_type=cognitive_signal[:80],
                source_concept_kind="evaluated_internal_thought",
                source_concept_method="advanced_thought_evaluator",
                source_concept_ref=(
                    f"thought:{evaluated_thought.get('origin_thought_id')}"[:240]
                    if evaluated_thought.get('origin_thought_id') else ""
                ),
            ))
            if accepted:
                result['created_goals'].append(new_goal['id'])
        
        # 3. Check for goals to merge (similar goals created from different thoughts)
        if len(goals) > 1:
            merged = self._merge_similar_goals(goals)
            result['merged_goals'].extend(merged)

        if result['updated_goals'] or result['merged_goals']:
            engine.reload_from_disk()
        
        return result
    
    def boost_goal_priority(
        self, 
        goal_id: str, 
        boost_factor: float,
        reason: str = ""
    ) -> bool:
        """
        Boost priority of an existing goal.
        
        Used when:
        - New thought reinforces existing goal
        - Goal becomes more urgent
        - External event makes goal more important
        """
        goals_data = self._load_goals_data()
        
        _raw_goals = goals_data.get('goals', {})
        _goals_iter = list(_raw_goals.values()) if isinstance(_raw_goals, dict) else _raw_goals
        for goal in _goals_iter:
            if goal.get('id') == goal_id:
                old_priority = goal.get('priority', 0.5)
                new_priority = min(1.0, old_priority + boost_factor)
                
                goal['priority'] = new_priority
                goal['priority_boosted'] = True
                goal['priority_history'] = goal.get('priority_history', [])
                goal['priority_history'].append({
                    'old': old_priority,
                    'new': new_priority,
                    'boost': boost_factor,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                
                self._save_goals_data(goals_data)
                return True
        
        return False
    
    def link_thought_to_goal(
        self,
        thought_id: str,
        goal_id: str,
        link_strength: float = 1.0
    ) -> bool:
        """
        Explicitly link a thought to a goal.
        
        Creates bidirectional link:
        - Thought → Goal (this thought supports this goal)
        - Goal → Thought (this goal originated from these thoughts)
        """
        # Update goal with thought link
        goals_data = self._load_goals_data()
        
        _raw_goals = goals_data.get('goals', {})
        _goals_iter = list(_raw_goals.values()) if isinstance(_raw_goals, dict) else _raw_goals
        for goal in _goals_iter:
            if goal.get('id') == goal_id:
                if 'origin_thoughts' not in goal:
                    goal['origin_thoughts'] = []
                
                goal['origin_thoughts'].append({
                    'thought_id': thought_id,
                    'link_strength': link_strength,
                    'linked_at': datetime.now().isoformat()
                })
                
                self._save_goals_data(goals_data)
                return True
        
        return False
    
    def get_goal_genealogy(self, goal_id: str) -> Dict:
        """
        Get the full genealogy of a goal:
        - Which thoughts created it
        - Which thoughts reinforced it
        - How priority evolved
        - Merge history
        """
        goals_data = self._load_goals_data()
        
        _raw_goals = goals_data.get('goals', {})
        _goals_iter = list(_raw_goals.values()) if isinstance(_raw_goals, dict) else _raw_goals
        for goal in _goals_iter:
            if goal.get('id') == goal_id:
                return {
                    'goal_id': goal_id,
                    'created_at': goal.get('created_at', ''),
                    'origin_thoughts': goal.get('origin_thoughts', []),
                    'priority_history': goal.get('priority_history', []),
                    'merge_history': goal.get('merge_history', []),
                    'current_priority': goal.get('priority', 0.5),
                    'status': goal.get('status', 'unknown')
                }
        
        return {}
    
    def _find_similar_goal(
        self, 
        evaluated_thought: Dict, 
        goals: List[Dict]
    ) -> Optional[Dict]:
        """
        Consume the matched-goal receipt produced by AdvancedThoughtEvaluator.

        This preserves causal provenance and avoids a second, language-specific
        comparison in the downstream linker.
        """
        goal_id = str(evaluated_thought.get("related_goal_id") or "")
        evaluation = evaluated_thought.get("evaluation", {})
        if not isinstance(evaluation, dict):
            return None
        if str(evaluation.get("related_goal_id") or "") != goal_id:
            return None
        try:
            similarity = float(evaluation.get("goal_similarity", 0.0))
        except (AttributeError, TypeError, ValueError, OverflowError):
            similarity = 0.0
        if not goal_id or not similarity > 0.4:
            return None

        for goal in goals:
            if str(goal.get("id") or "") == goal_id and goal.get("status") == "active":
                return goal
        return None
    
    def _update_goal_from_thought(self, goal: Dict, evaluated_thought: Dict):
        """
        Update an existing goal based on new thought.
        """
        # Boost priority if thought is urgent
        urgency = evaluated_thought.get('urgency', 0)
        if urgency > 0.7:
            boost = urgency * self.urgency_boost_factor
            self.boost_goal_priority(
                goal['id'],
                boost,
                reason=f"High urgency thought ({urgency:.2f})"
            )
        
        # Link thought to goal
        thought_id = evaluated_thought.get('origin_thought_id', '')
        if thought_id:
            self.link_thought_to_goal(thought_id, goal['id'])
    
    def _create_goal_from_thought(self, evaluated_thought: Dict) -> Dict:
        """
        Create a new goal from an evaluated thought.
        """
        concepts = evaluated_thought.get('concepts', ['unknown'])
        primary_concept = concepts[0] if concepts else 'unknown'
        
        goal_id = f"goal_{datetime.now().timestamp()}"
        
        goal = {
            'id': goal_id,
            'name': f"{evaluated_thought['type']}_{primary_concept}".replace(' ', '_'),
            'description': f"Goal created from thought about {primary_concept}",
            'type': evaluated_thought['type'],
            'priority': evaluated_thought.get('priority', 0.5),
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'origin': 'thought_goal_linker',
            'origin_thoughts': [{
                'thought_id': evaluated_thought.get('origin_thought_id', ''),
                'link_strength': 1.0,
                'linked_at': datetime.now().isoformat()
            }],
            'metadata': {
                'concepts': concepts,
                'urgency': evaluated_thought.get('urgency', 0),
                'actionability': evaluated_thought.get('actionability', 0),
                'goal_impact': evaluated_thought.get('goal_impact', 0),
                'source': 'advanced_thought_evaluator',
                'version': '2.0'
            }
        }
        
        return goal
    
    def _merge_similar_goals(self, goals: List[Dict]) -> List[str]:
        """
        Merge goals that are too similar.
        
        Returns list of merged goal IDs.
        """
        merged = []
        active = [goal for goal in goals if goal.get("status") == "active"]
        texts = [str(goal.get("name") or goal.get("description") or "") for goal in active]
        similarities = self._compute_semantic_similarity_matrix(texts)
        if similarities is None:
            return merged

        for i, goal1 in enumerate(active):
            for j in range(i + 1, len(active)):
                goal2 = active[j]
                if float(similarities[i, j]) > self.merge_threshold:
                    self._merge_goals(goal1, goal2)
                    merged.append(goal2["id"])
        return merged
    
    def _compute_goal_similarity(self, goal1: Dict, goal2: Dict) -> float:
        """Compare two goal descriptions only in calibrated Nomic space."""
        matrix = self._compute_semantic_similarity_matrix([
            str(goal1.get("name") or goal1.get("description") or ""),
            str(goal2.get("name") or goal2.get("description") or ""),
        ])
        if matrix is None:
            return 0.0
        return float(matrix[0, 1])

    @staticmethod
    def _compute_semantic_similarity_matrix(texts: List[str]):
        """Return cosine similarities only for calibrated Nomic vectors."""
        usable = [str(text).strip() for text in texts]
        if len(usable) < 2 or any(not text for text in usable):
            return None
        try:
            import numpy as np
            from utils.shared_embedder import get_embedder, is_calibrated_quality_space

            embedder = get_embedder(quality=True)
            if not hasattr(embedder, "encode_with_metadata"):
                return None
            encoded, space_id = embedder.encode_with_metadata(usable)
            if not is_calibrated_quality_space(space_id):
                return None
            vectors = np.asarray(encoded, dtype="float32")
            if vectors.ndim != 2 or vectors.shape[0] != len(usable) or not np.isfinite(vectors).all():
                return None
            norms = np.linalg.norm(vectors, axis=1)
            if np.any(norms <= 1e-9):
                return None
            normalized = vectors / norms[:, None]
            return np.clip(normalized @ normalized.T, 0.0, 1.0)
        except Exception:
            return None
    
    def _merge_goals(self, target_goal: Dict, source_goal: Dict):
        """
        Merge source_goal into target_goal.
        """
        goals_data = self._load_goals_data()

        # goals may be a dict {id: goal_obj} or a list
        raw = goals_data.get('goals', {})
        goals_iter = raw.values() if isinstance(raw, dict) else raw

        for goal in goals_iter:
            if goal.get('id') == target_goal['id']:
                # Merge priority (take max)
                goal['priority'] = max(
                    goal.get('priority', 0.5),
                    source_goal.get('priority', 0.5)
                )
                
                # Merge origin thoughts
                if 'origin_thoughts' not in goal:
                    goal['origin_thoughts'] = []
                
                goal['origin_thoughts'].extend(
                    source_goal.get('origin_thoughts', [])
                )
                
                # Add merge history
                if 'merge_history' not in goal:
                    goal['merge_history'] = []
                
                goal['merge_history'].append({
                    'merged_goal_id': source_goal['id'],
                    'merged_goal_name': source_goal.get('name', ''),
                    'merged_at': datetime.now().isoformat(),
                    'reason': 'high_similarity'
                })
            
            elif goal.get('id') == source_goal['id']:
                # Mark source as merged
                goal['status'] = 'merged'
                goal['merged_into'] = target_goal['id']
                goal['merged_at'] = datetime.now().isoformat()
        
        self._save_goals_data(goals_data)
    
    def _add_goal(self, goal: Dict):
        """Add a new goal to goals.json."""
        goals_data = self._load_goals_data()

        raw = goals_data.get('goals', {})
        if isinstance(raw, list):
            # Migrate list → dict on first write
            raw = {g.get('id', str(i)): g for i, g in enumerate(raw)}
        if 'goals' not in goals_data or not isinstance(goals_data['goals'], dict):
            goals_data['goals'] = raw

        goal_id = goal.get('id', f"goal_{int(__import__('time').time())}")
        goals_data['goals'][goal_id] = goal

        self._save_goals_data(goals_data)

    def _load_goals(self) -> List[Dict]:
        """Load all goals."""
        raw = self._load_goals_data().get('goals', {})
        if isinstance(raw, dict):
            return list(raw.values())
        return raw if isinstance(raw, list) else []
    
    def _load_goals_data(self) -> Dict:
        """Load goals.json via DAL."""
        try:
            from core.data.access import DataAccess
            dal = DataAccess(str(self.persona_dir))
            goals_list = dal.get_goals()
            goals_dict = {g['id']: g for g in goals_list}
            return {'goals': goals_dict, '_dal': dal}
        except Exception:
            goals_file = self.persona_dir / 'goals.json'
            if not goals_file.exists():
                return {'goals': {}}
            try:
                with open(goals_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {'goals': {}}
    
    def _save_goals_data(self, data: Dict):
        """Save goals.json via DAL (atomic)."""
        try:
            from core.data.access import DataAccess
            dal = data.get('_dal') or DataAccess(str(self.persona_dir))
            raw = data.get('goals', {})
            goals_iter = raw.values() if isinstance(raw, dict) else raw
            for goal in goals_iter:
                if isinstance(goal, dict):
                    dal.save_goal(goal)
            return
        except Exception:
            pass
        # Fallback: atomic raw write
        import os
        goals_file = self.persona_dir / 'goals.json'
        tmp = goals_file.with_suffix('.tmp')
        clean = {k: v for k, v in data.items() if k != '_dal'}
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
        os.replace(tmp, goals_file)

if __name__ == "__main__":
    print("="*70)
    print("THOUGHT-GOAL LINKER TEST")
    print("="*70)
    
    linker = ThoughtGoalLinker('data/persona')
    
    # Test with sample evaluated thought
    test_thought = {
        'type': 'uncertainty',
        'concept': 'consciousness',
        'priority': 0.75,
        'urgency': 0.68,
        'actionability': 0.82,
        'goal_impact': 0.70,
        'origin_thought_id': 'th_test_001',
        'concepts': ['consciousness', 'awareness', 'self']
    }
    
    result = linker.process_thought_evaluation(test_thought)
    
    print(f"\nProcessing Result:")
    print(f"  Created goals: {len(result['created_goals'])}")
    print(f"  Updated goals: {len(result['updated_goals'])}")
    print(f"  Linked goals: {len(result['linked_goals'])}")
    print(f"  Merged goals: {len(result['merged_goals'])}")
    
    if result['created_goals']:
        print(f"\n  New goal ID: {result['created_goals'][0]}")
        genealogy = linker.get_goal_genealogy(result['created_goals'][0])
        print(f"  Genealogy: {json.dumps(genealogy, indent=4)}")
    
    print("\n" + "="*70)
    print("✅ Thought-Goal Linker Test Complete")
    print("="*70)
