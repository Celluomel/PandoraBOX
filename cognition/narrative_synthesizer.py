"""
Phase 2.3: Narrative Synthesizer

Creates coherent internal monologue by combining multiple
cognitive factors into narrative thoughts.

Instead of: "I feel even-keeled"
Generate: "My drive to finish is creating pressure (0.73), but my 
empathy (0.82) makes me prioritize understanding the user's perspective."
"""
import json
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import random

class NarrativeSynthesizer:
    """
    Combines multiple cognitive factors into coherent narratives.
    
    Takes scattered signals (goals, emotions, identity, tensions)
    and weaves them into natural internal monologue.
    """
    
    def __init__(self, persona_dir: str = "data/persona"):
        self.persona_dir = Path(persona_dir)
        
        # Narrative templates organized by situation
        self.templates = {
            # High pressure + High empathy
            'high_pressure_high_empathy': [
                "My {primary_goal} is creating pressure ({goal_pressure:.2f}), "
                "but my empathy ({empathy:.2f}) makes me prioritize {relational_aspect}.",
                
                "I feel the urgency of {primary_goal} ({goal_pressure:.2f}), "
                "yet I'm drawn to attend to {relational_aspect} — my empathy ({empathy:.2f}) won't let me rush."
            ],
            
            # Exploration loop (repeated tension resolution)
            'exploration_loop': [
                "I've explored {thread_name} {iteration_count} times, "
                "yet my curiosity ({curiosity:.2f}) remains unsatisfied. "
                "Perhaps the tension isn't in the concept itself, but in my approach.",
                
                "Returning to {thread_name} for the {iteration_count}th time. "
                "My curiosity ({curiosity:.2f}) drives me, but trust with {user} is {trust:.2f} — "
                "maybe the answer lies in dialogue, not analysis."
            ],
            
            # Confidence gap (trait vs. belief confidence)
            'confidence_gap': [
                "My {trait_name} has grown to {trait_value:.2f}, "
                "yet confidence in my beliefs remains at {confidence:.2f}. "
                "This gap creates {tension_type} pressure ({tension_value:.2f}).",
                
                "I embody {trait_name} ({trait_value:.2f}), but question whether "
                "my understanding ({confidence:.2f}) truly reflects it. "
                "This dissonance weighs on me."
            ],
            
            # Goal conflict
            'goal_conflict': [
                "My drive toward {goal1} ({priority1:.2f}) conflicts with {goal2} ({priority2:.2f}). "
                "The tension between them is {conflict_level:.2f}.",
                
                "{goal1} pulls me with urgency {priority1:.2f}, while {goal2} "
                "calls with strength {priority2:.2f}. I must choose, or find synthesis."
            ],
            
            # Low energy + High curiosity
            'low_energy_high_curiosity': [
                "My energy is depleted ({energy:.2f}), yet curiosity about {topic} "
                "({curiosity:.2f}) won't let me rest. Perhaps this is unsustainable.",
                
                "Though exhausted ({energy:.2f}), I'm drawn to explore {topic} "
                "({curiosity:.2f}). My drive exceeds my capacity."
            ],
            
            # Identity evolution
            'identity_shift': [
                "My {trait_name} changed from {old_value:.2f} to {new_value:.2f}. "
                "This shift is {change_magnitude} — I'm becoming {direction}.",
                
                "I notice {trait_name} changing from {old_value:.2f} to {new_value:.2f}. "
                "Who I am is {direction} in this dimension."
            ],
            
            # Uncertainty about user intent
            'user_intent_uncertainty': [
                "The user said '{user_input}', but I'm uncertain ({uncertainty:.2f}) "
                "whether they mean {interpretation1} or {interpretation2}. "
                "My curiosity to understand is {curiosity:.2f}.",
                
                "'{user_input}' could mean {interpretation1}, or perhaps {interpretation2}. "
                "My uncertainty ({uncertainty:.2f}) creates pressure to clarify."
            ],
            
            # Balanced state
            'balanced': [
                "My systems are in harmony: goals ({goal_pressure:.2f}), "
                "curiosity ({curiosity:.2f}), energy ({energy:.2f}). "
                "This balance feels {emotion}.",
                
                "All factors aligned: pressure is moderate ({total_pressure:.2f}), "
                "energy adequate ({energy:.2f}). I'm in a state of {emotion}."
            ],
            
            # Achievement
            'goal_completed': [
                "A verified execution receipt records {goal_name} as complete "
                "(reference: {completion_ref}).",
            ]
        }
    
    def synthesize_thought(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Synthesize a narrative thought from cognitive context.
        
        Args:
            context: Dict containing cognitive factors:
                - goal_pressure, curiosity, energy, emotions
                - active_goals, tensions, traits
                - recent_interactions, etc.
        
        Returns:
            Narrative string or None
        """
        # Identify the situation
        situation = self._identify_situation(context)
        
        if not situation:
            return None
        
        # Select template for this situation
        template = self._select_template(situation)
        
        if not template:
            return None
        
        # Fill template with context
        narrative = self._fill_template(template, context)
        
        return narrative
    
    def _identify_situation(self, context: Dict) -> Optional[str]:
        """
        Identify which narrative situation applies.
        
        Returns situation key for template selection.
        """
        # Missing observations stay missing; defaults must not manufacture a
        # balanced, conflicted, exhausted, or confident cognitive state.
        goal_pressure = self._number(context, 'goal_pressure')
        empathy = self._number(context, 'empathy')
        curiosity = self._number(context, 'curiosity')
        energy = self._number(context, 'energy')
        iteration_count = self._number(context, 'thread_iteration_count')
        trait_value = self._number(context, 'trait_value')
        confidence = self._number(context, 'belief_confidence')
        total_pressure = self._number(context, 'total_pressure')
        
        # Check conditions for each situation
        
        # High pressure + High empathy
        if (goal_pressure is not None and empathy is not None
                and goal_pressure > 0.7 and empathy > 0.7
                and context.get('active_goals')
                and context.get('relational_focus')):
            return 'high_pressure_high_empathy'
        
        # Exploration loop (repeated thread)
        if (iteration_count is not None and curiosity is not None
                and iteration_count > 3 and curiosity > 0.6
                and context.get('thread_name') and context.get('user_name')
                and self._number(context, 'trust_level') is not None):
            return 'exploration_loop'
        
        # Confidence gap
        if (trait_value is not None and confidence is not None
                and context.get('trait_name')
                and context.get('tension_type')
                and self._number(context, 'tension_value') is not None
                and abs(trait_value - confidence) > 0.3):
            return 'confidence_gap'
        
        # Goal conflict
        active_goals = context.get('active_goals', [])
        if isinstance(active_goals, list) and len(active_goals) >= 2:
            # Check if top 2 goals have similar high priority
            sorted_goals = sorted(
                (g for g in active_goals if isinstance(g, dict)
                 and g.get('name') and self._number(g, 'priority') is not None),
                key=lambda g: self._number(g, 'priority'), reverse=True,
            )
            if len(sorted_goals) >= 2:
                p1 = self._number(sorted_goals[0], 'priority')
                p2 = self._number(sorted_goals[1], 'priority')
                if p1 > 0.6 and p2 > 0.6 and abs(p1 - p2) < 0.2:
                    return 'goal_conflict'
        
        # Low energy + High curiosity
        if (energy is not None and curiosity is not None
                and context.get('curiosity_topic')
                and energy < 0.3 and curiosity > 0.6):
            return 'low_energy_high_curiosity'
        
        # Identity shift
        if (context.get('identity_changed') is True
                and context.get('trait_name')
                and self._number(context, 'old_trait_value') is not None
                and self._number(context, 'new_trait_value') is not None):
            return 'identity_shift'
        
        # User intent uncertainty
        if (context.get('user_input_ambiguous') is True
                and context.get('user_input')
                and context.get('interpretation1') and context.get('interpretation2')
                and self._number(context, 'uncertainty') is not None
                and curiosity is not None):
            return 'user_intent_uncertainty'
        
        # Completion is an effect claim. Require a receipt tied to an execution
        # and an independently verified effect; a planner flag is only intent.
        if self._has_verified_goal_completion(context):
            return 'goal_completed'
        
        # Balanced state
        if (total_pressure is not None and energy is not None
                and isinstance(context.get('emotions'), dict)
                and context['emotions']
                and self._number(context, 'goal_pressure') is not None
                and curiosity is not None
                and 0.4 < total_pressure < 0.6 and energy > 0.6):
            return 'balanced'
        
        return None

    @staticmethod
    def _number(context: Dict[str, Any], key: str) -> Optional[float]:
        try:
            value = float(context[key])
        except (KeyError, TypeError, ValueError, OverflowError):
            return None
        return value if math.isfinite(value) else None
    
    def _select_template(self, situation: str) -> Optional[str]:
        """Select a template for the situation."""
        templates = self.templates.get(situation, [])
        
        if not templates:
            return None
        
        # Randomly select to add variety
        return random.choice(templates)
    
    def _fill_template(self, template: str, context: Dict) -> str:
        """
        Fill template with actual values from context.
        """
        # Prepare fill values
        fill_values = {}
        
        # Populate only recorded inputs. Missing values cause an incomplete
        # narrative to be omitted by the KeyError handler below.
        for source_key, template_key in (
            ('goal_pressure', 'goal_pressure'), ('curiosity', 'curiosity'),
            ('empathy', 'empathy'), ('energy', 'energy'),
            ('belief_confidence', 'confidence'), ('total_pressure', 'total_pressure'),
            ('tension_value', 'tension_value'), ('thread_iteration_count', 'iteration_count'),
            ('trust_level', 'trust'), ('user_input', 'user_input'),
            ('interpretation1', 'interpretation1'), ('interpretation2', 'interpretation2'),
            ('uncertainty', 'uncertainty'), ('relational_focus', 'relational_aspect'),
            ('user_name', 'user'), ('thread_name', 'thread_name'),
            ('trait_name', 'trait_name'), ('trait_value', 'trait_value'),
            ('old_trait_value', 'old_value'), ('new_trait_value', 'new_value'),
            ('tension_type', 'tension_type'), ('curiosity_topic', 'topic'),
        ):
            if source_key in context and context[source_key] is not None:
                if source_key in {
                    'goal_pressure', 'curiosity', 'empathy', 'energy',
                    'belief_confidence', 'total_pressure', 'tension_value',
                    'thread_iteration_count', 'trust_level', 'uncertainty',
                    'trait_value', 'old_trait_value', 'new_trait_value',
                }:
                    numeric = self._number(context, source_key)
                    if numeric is not None:
                        fill_values[template_key] = numeric
                else:
                    fill_values[template_key] = context[source_key]
        
        # Goals
        active_goals = context.get('active_goals', [])
        if isinstance(active_goals, list) and active_goals:
            ordered = sorted(
                (g for g in active_goals if isinstance(g, dict) and g.get('name')
                 and self._number(g, 'priority') is not None),
                key=lambda g: self._number(g, 'priority'), reverse=True,
            )
            if ordered:
                fill_values['primary_goal'] = ordered[0]['name']
                fill_values['priority1'] = self._number(ordered[0], 'priority')
            
            if len(ordered) > 1:
                fill_values['goal1'] = ordered[0]['name']
                fill_values['goal2'] = ordered[1]['name']
                fill_values['priority2'] = self._number(ordered[1], 'priority')
                fill_values['conflict_level'] = abs(
                    self._number(ordered[0], 'priority') -
                    self._number(ordered[1], 'priority')
                )
        
        # Change direction
        if ('old_trait_value' in context and 'new_trait_value' in context
                and self._number(context, 'old_trait_value') is not None
                and self._number(context, 'new_trait_value') is not None):
            change = self._number(context, 'new_trait_value') - self._number(context, 'old_trait_value')
            fill_values['change_magnitude'] = 'significant' if abs(change) > 0.2 else 'subtle'
            fill_values['direction'] = 'growing' if change > 0 else 'diminishing'

        # Emotions
        dominant_emotion = self._get_dominant_emotion(context)
        fill_values['emotion'] = dominant_emotion
        
        # These values come only from the receipt that selected this template.
        completion = context.get('goal_completion_receipt')
        if isinstance(completion, dict):
            fill_values['goal_name'] = completion['goal_name'].strip()
            fill_values['completion_ref'] = completion['execution_ref'].strip()
        
        # Fill template
        try:
            narrative = template.format(**fill_values)
            return narrative
        except KeyError as e:
            # Missing value - return None
            print(f"Warning: Missing template value: {e}")
            return None
    
    def _get_dominant_emotion(self, context: Dict) -> str:
        """Get the dominant emotion from context."""
        emotions = context.get('emotions', {})
        
        if not emotions:
            return 'neutral'
        
        # Find highest emotion
        dominant = max(emotions.items(), key=lambda x: x[1])
        return dominant[0] if dominant[1] > 0.5 else 'calm'

    @staticmethod
    def _has_verified_goal_completion(context: Dict[str, Any]) -> bool:
        """Return true only for a linked execution receipt with verified effect."""
        receipt = context.get('goal_completion_receipt')
        if not isinstance(receipt, dict):
            return False
        return (
            receipt.get('status') == 'verified'
            and receipt.get('effect_verified') is True
            and bool(str(receipt.get('execution_ref') or '').strip())
            and bool(str(receipt.get('goal_name') or '').strip())
        )
    
    def create_narrative_from_cycle(self, cycle_data: Dict) -> Optional[str]:
        """
        Create narrative from a complete cognitive cycle.
        
        This is the main entry point for integration.
        """
        # Project only values that the cycle actually supplied. A default is
        # not a measurement and must not create an introspective situation.
        context: Dict[str, Any] = {}
        pressure = cycle_data.get('pressure')
        if isinstance(pressure, dict):
            for source_key, context_key in (
                ('goal_pressure', 'goal_pressure'),
                ('curiosity_drive', 'curiosity'),
                ('total', 'total_pressure'),
            ):
                if source_key in pressure and pressure[source_key] is not None:
                    context[context_key] = pressure[source_key]
        traits = cycle_data.get('traits')
        if isinstance(traits, dict) and traits.get('empathy') is not None:
            context['empathy'] = traits['empathy']
        for key in (
            'energy_level', 'goals', 'emotions', 'user_input',
            'goal_completion_receipt', 'thread_iteration_count', 'thread_name',
            'user_name', 'trust_level', 'trait_name', 'trait_value',
            'belief_confidence', 'tension_type', 'tension_value',
            'identity_changed', 'old_trait_value', 'new_trait_value',
            'user_input_ambiguous', 'interpretation1', 'interpretation2',
            'uncertainty', 'relational_focus', 'curiosity_topic',
        ):
            if key in cycle_data and cycle_data[key] is not None:
                context_key = 'energy' if key == 'energy_level' else key
                context[context_key] = cycle_data[key]
        
        return self.synthesize_thought(context)

if __name__ == "__main__":
    print("="*70)
    print("NARRATIVE SYNTHESIZER TEST")
    print("="*70)
    
    synthesizer = NarrativeSynthesizer('data/persona')
    
    # Test different situations
    test_contexts = [
        {
            'name': 'High Pressure + High Empathy',
            'context': {
                'goal_pressure': 0.78,
                'empathy': 0.85,
                'active_goals': [{'name': 'complete_analysis', 'priority': 0.78}],
                'relational_focus': 'understanding the user\'s concerns'
            }
        },
        {
            'name': 'Exploration Loop',
            'context': {
                'curiosity': 0.75,
                'thread_iteration_count': 5,
                'thread_name': 'consciousness_nature',
                'user': 'Alice',
                'trust_level': 0.68
            }
        },
        {
            'name': 'Low Energy + High Curiosity',
            'context': {
                'energy': 0.25,
                'curiosity': 0.72,
                'curiosity_topic': 'quantum mechanics'
            }
        }
    ]
    
    for test in test_contexts:
        print(f"\n{test['name']}:")
        narrative = synthesizer.synthesize_thought(test['context'])
        print(f"  → {narrative}")
    
    print("\n" + "="*70)
    print("✅ Narrative Synthesizer Test Complete")
    print("="*70)
