"""
Phase 2.1: Advanced Thought Evaluator

Consumes producer-owned thought signals and structured topics, then applies
calibrated semantic similarity and numeric evidence. It never classifies
free prose with word lists.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import math

class AdvancedThoughtEvaluator:
    """
    Advanced thought evaluation using semantic understanding.
    
    Improvements over simple evaluator:
    - Calibrated semantic similarity to active goals
    - Conceptual friction detection (conflicting concepts)
    - Multi-factor priority scoring (urgency × impact × actionability)
    - Goal impact prediction
    - Better type classification
    """
    
    def __init__(self, persona_dir: str = "data/persona"):
        self.persona_dir = Path(persona_dir)
        
        # Semantic similarity thresholds
        self.high_similarity_threshold = 0.7
        self.moderate_similarity_threshold = 0.4
    
    def evaluate_recent_thoughts(self, max_thoughts: int = 10) -> List[Dict]:
        """
        Evaluate recent thoughts using advanced semantic analysis.
        
        Returns list of goal suggestions with enhanced metadata.
        """
        thoughts = self._load_recent_thoughts(max_thoughts)
        
        if not thoughts:
            return []
        
        # Load active goals for semantic comparison
        active_goals = self._load_active_goals()
        
        suggestions = []
        
        for thought in thoughts:
            # Skip already processed thoughts
            if thought.get('evaluated', False):
                continue
            
            evaluation = self._evaluate_thought_advanced(thought, active_goals)
            
            # Only create suggestion if actionable
            if evaluation['actionability'] > 0.5:
                suggestion = self._create_goal_suggestion(thought, evaluation)
                suggestions.append(suggestion)

            # Persist a completed evaluation even when it produces no goal;
            # otherwise the same low-signal thoughts are recomputed each cycle.
            self._mark_thought_evaluated(thought.get('id', ''))
        
        return suggestions
    
    def _evaluate_thought_advanced(
        self, 
        thought: Dict, 
        active_goals: List[Dict]
    ) -> Dict:
        """
        Advanced evaluation using multiple factors.
        """
        # 1. Classify only producer-owned schema metadata.
        thought_type, type_confidence = self._classify_thought_advanced(thought)

        # 2. The producer's topic is the concept contract; do not mine prose.
        concepts = self._extract_concepts(thought)
        
        # 3. Compute semantic similarity to active goals
        goal_match = self._compute_goal_match(concepts, active_goals)
        goal_similarity = goal_match["similarity"]
        
        # 4. Detect conceptual friction
        friction_score = self._detect_conceptual_friction(thought)
        
        # 5. Compute multi-factor priority
        priority = self._compute_priority_multifactor(
            type_confidence=type_confidence,
            goal_similarity=goal_similarity,
            friction_score=friction_score
        )
        
        # 6. Compute urgency (time-sensitive vs. exploratory)
        urgency = self._compute_urgency(thought_type, friction_score)
        
        # 7. Compute actionability
        actionability = self._compute_actionability(
            thought_type=thought_type,
            concepts=concepts,
            goal_similarity=goal_similarity
        )
        
        # 8. Predict goal impact
        goal_impact = self._predict_goal_impact(
            goal_similarity=goal_similarity,
            priority=priority
        )
        
        return {
            'type': thought_type,
            'type_confidence': type_confidence,
            'concepts': concepts,
            'goal_similarity': goal_similarity,
            'related_goal_id': goal_match["goal_id"],
            'friction_score': friction_score,
            'priority': priority,
            'urgency': urgency,
            'actionability': actionability,
            'goal_impact': goal_impact
        }
    
    def _classify_thought_advanced(self, thought: Dict) -> tuple:
        """Return a schema signal and its explicit producer confidence."""
        from cognition.thought_signals import signal_for_thought

        signal = signal_for_thought(thought)
        if signal is None:
            return "general", 0.0
        try:
            confidence = float(thought.get("cognitive_signal_confidence", 1.0))
        except (TypeError, ValueError, OverflowError):
            confidence = 0.0
        if not math.isfinite(confidence):
            confidence = 0.0
        return signal, max(0.0, min(1.0, confidence))

    @staticmethod
    def _extract_concepts(thought: Dict) -> List[str]:
        """Return only the producer's structured topic/concept fields."""
        raw = thought.get("topic") or thought.get("concept")
        if isinstance(raw, str) and raw.strip():
            return [" ".join(raw.replace("_", " ").split())[:240]]
        return []
    
    def _compute_goal_similarity(
        self,
        concepts: List[str],
        active_goals: List[Dict]
    ) -> float:
        return self._compute_goal_match(concepts, active_goals)["similarity"]

    def _compute_goal_match(
        self,
        concepts: List[str],
        active_goals: List[Dict],
    ) -> Dict[str, Any]:
        """
        Return the best active goal ID and similarity from one calibrated batch.

        Use cosine similarity only when the calibrated Nomic space produced
        the vectors. An unavailable or uncalibrated embedding result contributes
        no semantic similarity; it never falls back to token overlap.
        """
        if not concepts or not active_goals:
            return {"goal_id": None, "similarity": 0.0}
        concept_text = ' '.join(concepts)
        goals = [
            (str(goal.get("id") or ""), str(goal.get("name") or goal.get("description") or ""))
            for goal in active_goals
        ]
        goals = [(goal_id, text) for goal_id, text in goals if text]
        if not goals:
            return {"goal_id": None, "similarity": 0.0}
        try:
            import numpy as np
            from utils.shared_embedder import (
                get_embedder, is_calibrated_quality_space,
            )
            emb = get_embedder(quality=True)
            texts = [concept_text] + [text for _, text in goals]
            if hasattr(emb, "encode_with_metadata"):
                encoded, space_id = emb.encode_with_metadata(texts)
                if not is_calibrated_quality_space(space_id):
                    return {"goal_id": None, "similarity": 0.0}
            else:
                return {"goal_id": None, "similarity": 0.0}
            vecs = np.asarray(encoded, dtype="float32")
            if vecs.ndim != 2 or vecs.shape[0] != len(texts) or not np.isfinite(vecs).all():
                return {"goal_id": None, "similarity": 0.0}
            c = vecs[0]
            others = vecs[1:]
            cn = float(np.linalg.norm(c)) + 1e-9
            on = np.linalg.norm(others, axis=1) + 1e-9
            sims = (others @ c) / (on * cn)
            if not len(sims):
                return {"goal_id": None, "similarity": 0.0}
            best_index = int(np.argmax(sims))
            return {
                "goal_id": goals[best_index][0] or None,
                "similarity": float(min(1.0, max(0.0, float(sims[best_index])))),
            }
        except Exception:
            return {"goal_id": None, "similarity": 0.0}

    @staticmethod
    def _detect_conceptual_friction(thought: Dict) -> float:
        """Use the producer's numeric friction measurement, never phrasing."""
        try:
            score = float(thought.get("conceptual_friction", 0.0))
        except (TypeError, ValueError, OverflowError):
            return 0.0
        return max(0.0, min(1.0, score)) if math.isfinite(score) else 0.0
    
    def _compute_priority_multifactor(
        self,
        type_confidence: float,
        goal_similarity: float,
        friction_score: float
    ) -> float:
        """
        Compute priority from multiple factors.
        
        Priority = weighted combination of:
        - Type confidence (40%)
        - Goal similarity (40%)
        - Friction score (20%)
        """
        priority = (
            type_confidence * 0.4 +
            goal_similarity * 0.4 +
            friction_score * 0.2
        )
        
        return min(1.0, priority)
    
    def _compute_urgency(self, thought_type: str, friction_score: float) -> float:
        """
        Compute urgency (how time-sensitive is this thought).
        
        Tension thoughts with high friction are most urgent.
        """
        base_urgency = {
            'tension': 0.8,
            'uncertainty': 0.5,
            'opportunity': 0.4,
            'general': 0.3
        }.get(thought_type, 0.3)
        
        # Friction increases urgency
        urgency = base_urgency + (friction_score * 0.2)
        
        return min(1.0, urgency)
    
    def _compute_actionability(
        self,
        thought_type: str,
        concepts: List[str],
        goal_similarity: float
    ) -> float:
        """
        Compute how actionable this thought is.
        
        More concepts + higher goal similarity = more actionable.
        """
        # Similarity is relevance evidence, not evidence that a thought
        # requests or supports action. Require a producer-owned signal before
        # a Phase 2 suggestion can become a durable goal.
        if thought_type == "general":
            return 0.0

        # Base actionability by type
        base = {
            'opportunity': 0.8,
            'uncertainty': 0.6,
            'tension': 0.7,
            'general': 0.4
        }.get(thought_type, 0.4)
        
        # More concepts = more actionable
        concept_factor = min(1.0, len(concepts) / 5.0)
        
        # Higher goal similarity = more actionable
        actionability = (base * 0.5) + (concept_factor * 0.2) + (goal_similarity * 0.3)
        
        return min(1.0, actionability)
    
    def _predict_goal_impact(self, goal_similarity: float, priority: float) -> float:
        """
        Predict impact on existing goals if this thought becomes a goal.
        """
        # Simple prediction: high similarity × high priority = high impact
        impact = (goal_similarity * 0.6) + (priority * 0.4)
        
        return min(1.0, impact)
    
    def _create_goal_suggestion(self, thought: Dict, evaluation: Dict) -> Dict:
        """
        Create enhanced goal suggestion from thought evaluation.
        """
        concepts = evaluation['concepts']
        primary_concept = concepts[0] if concepts else 'unknown'
        
        suggestion = {
            'type': f"{evaluation['type']}_{primary_concept}".replace(' ', '_'),
            'cognitive_signal': evaluation['type'],
            'source': 'advanced_thought_evaluator',
            'concept': primary_concept,
            'related_goal_id': evaluation.get('related_goal_id'),
            'priority': evaluation['priority'],
            'urgency': evaluation['urgency'],
            'actionability': evaluation['actionability'],
            'goal_impact': evaluation['goal_impact'],
            'created_at': datetime.now().isoformat(),
            'origin_thought_id': thought.get('id', ''),
            'evaluation': {
                'type_confidence': evaluation['type_confidence'],
                'goal_similarity': evaluation['goal_similarity'],
                'related_goal_id': evaluation.get('related_goal_id'),
                'friction_score': evaluation['friction_score'],
                'concepts_extracted': len(concepts)
            },
            'metadata': {
                'source': 'advanced_thought_evaluator',
                'version': '2.0'
            }
        }
        
        return suggestion
    
    def _load_recent_thoughts(self, max_thoughts: int = 10) -> List[Dict]:
        """Load recent thoughts via DAL."""
        try:
            from core.data.access import DataAccess
            return DataAccess(str(self.persona_dir)).get_thoughts(limit=max_thoughts)
        except Exception:
            thought_stream_file = self.persona_dir / 'thought_stream.json'
            if not thought_stream_file.exists():
                return []
            try:
                with open(thought_stream_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    thoughts = data.get('thoughts', [])
                    return thoughts[-max_thoughts:] if thoughts else []
            except Exception:
                return []
    
    def _load_active_goals(self) -> List[Dict]:
        """Load active goals via DAL."""
        try:
            from core.data.access import DataAccess
            return DataAccess(str(self.persona_dir)).get_goals(status='active')
        except Exception:
            goals_file = self.persona_dir / 'goals.json'
            if not goals_file.exists():
                return []
            try:
                with open(goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    raw = data.get('goals', {})
                    goals = list(raw.values()) if isinstance(raw, dict) else raw
                    return [g for g in goals if g.get('status') == 'active']
            except Exception:
                return []
    
    def _mark_thought_evaluated(self, thought_id: str):
        """Mark a thought as evaluated via DAL (atomic update)."""
        if not thought_id:
            return
        try:
            from core.data.access import DataAccess
            dal = DataAccess(str(self.persona_dir))
            thoughts = dal.get_thoughts(skip_expired=False, limit=200)
            for t in thoughts:
                if t.get('id') == thought_id:
                    t['evaluated'] = True
                    t['evaluated_at'] = datetime.now().isoformat()
                    t['evaluator_version'] = '2.0_advanced'
                    dal.update_thought(t)
                    break
        except Exception:
            pass

if __name__ == "__main__":
    print("="*70)
    print("ADVANCED THOUGHT EVALUATOR TEST")
    print("="*70)
    
    evaluator = AdvancedThoughtEvaluator('data/persona')
    
    # Test evaluation
    suggestions = evaluator.evaluate_recent_thoughts()
    
    print(f"\nGenerated {len(suggestions)} goal suggestions:\n")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. Type: {suggestion['type']}")
        print(f"   Concept: {suggestion['concept']}")
        print(f"   Priority: {suggestion['priority']:.2f}")
        print(f"   Urgency: {suggestion['urgency']:.2f}")
        print(f"   Actionability: {suggestion['actionability']:.2f}")
        print(f"   Goal Impact: {suggestion['goal_impact']:.2f}")
        print(f"   Type Confidence: {suggestion['evaluation']['type_confidence']:.2f}")
        print(f"   Goal Similarity: {suggestion['evaluation']['goal_similarity']:.2f}")
        print(f"   Friction: {suggestion['evaluation']['friction_score']:.2f}")
        print()
    
    print("="*70)
    print("✅ Advanced Thought Evaluator Test Complete")
    print("="*70)
