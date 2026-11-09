"""Application State Management"""
import asyncio
import threading
import logging
import time
import os
import queue
from datetime import datetime
from pathlib import Path
from typing import Optional

import managers.settings_manager as _settings_mod
from managers.settings_manager import config, load_settings
from managers.llm_manager import create_llm_manager
from managers.memory_manager import create_memory_manager
from managers.audio_manager import create_audio_manager
from managers.conversational_audio import ConversationalAudioManager
from managers.vision_manager import StreamingVisionManager

logger = logging.getLogger(__name__)


def _init_persona(llm_generate_fn=None, llm_stream_fn=None):
    """
    Bootstrap PandoraBOX's EnhancedAISystem via PersonaBridge.
    Returns a PersonaBridge instance, or None on failure.
    """
    try:
        from cognition.persona_bridge import PersonaBridge
        persona = PersonaBridge(external_llm_fn=llm_generate_fn, external_llm_stream_fn=llm_stream_fn)
        if persona.is_ready:
            logger.info("✅ Persona (PandoraBOX cognitive engine) ready")
        else:
            logger.warning("⚠️  Persona initialised in degraded mode (no PandoraBOX)")
        return persona
    except Exception as e:
        logger.error(f"❌ Persona init failed: {e}")
        return None

def _cfg():
    """Always return the live config object (updated after every save)."""
    return _settings_mod.config

class AppState:
    def __init__(self):
        self.llm        = None
        self.memory     = None
        self.audio      = None
        self.conv_audio = None
        self.vision     = None
        self.presence_engine = None
        self.persona    = None   # PersonaBridge (PandoraBOX cognitive engine) — wired in initialize()
        self.tts_stop_event = threading.Event()
        self.ready      = False
        self.start_time = time.time()
        self.initializing = False
        self._vision_attached_to_cognition = False
        self._deferred_cognitive_tasks = set()
        
        # Thread-safe audio→UI queue
        self.transcription_queue = queue.Queue()

    async def initialize(self):
        if self.initializing:
            return
        
        self.initializing = True
        
        try:
            self.llm = create_llm_manager()
            logger.info(f"✅ LLM: {_cfg().LLM_PROVIDER}/{_cfg().LLM_MODEL}")
        except Exception as e:
            logger.error(f"LLM init failed: {e}")

        # ── Persona (PandoraBOX cognitive engine) ─────────────────────────────
        # Pass Robot's LLM fns so PandoraBOX shares the same backend:
        #   generate_bare — for PandoraBOX's internal cognitive tasks (dream, learning,
        #                   reflection). Calls the provider directly, NO history pollution,
        #                   temperature & max_tokens fully forwarded.
        #   generate_stream — for user-facing streaming responses (records history).
        try:
            llm_fn        = getattr(self.llm, "generate_bare",   None) if self.llm else None
            llm_stream_fn = getattr(self.llm, "generate_stream",  None) if self.llm else None
            # Fallback: if generate_bare unavailable (old provider), use plain generate
            if llm_fn is None:
                llm_fn = getattr(self.llm, "generate", None) if self.llm else None
                if llm_fn:
                    logger.warning("generate_bare not found on LLMManager — falling back to generate (history may be polluted by cognitive tasks)")
            self.persona = _init_persona(llm_generate_fn=llm_fn, llm_stream_fn=llm_stream_fn)
        except Exception as e:
            logger.error(f"Persona init failed (non-fatal): {e}")

        # ── Autonomous Orchestrator (v2) ───────────────────────────────────
        self.sce = None
        self.empathy_engine = None
        self.are = None
        self.acc = None   # Active Cognitive Context (CAG Layer 2)
        self.lumina_network = None
        self.orchestrator = None
        try:
            organism = getattr(self.persona, '_organism', None) if self.persona else None
            if organism is not None:
                from core.orchestrator import AutonomousOrchestrator
                self.orchestrator = AutonomousOrchestrator(
                    organism=organism,
                    workspace=getattr(organism, 'workspace', None),
                )
                # Wire messaging manager into execution layer (if configured later)
                organism.orchestrator = self.orchestrator
                logger.info("✅ Autonomous Orchestrator created (will start on first use)")
            else:
                logger.info("⚠️  Orchestrator skipped — organism not available yet")
        except Exception as e:
            logger.error(f"Orchestrator init failed (non-fatal): {e}")

        try:
            self.memory = create_memory_manager()
            logger.info(f"✅ Memory: {_cfg().MEMORY_BACKEND}")
        except Exception as e:
            logger.error(f"Memory init failed: {e}")

        # Initialize vision with retry logic
        vision_retries = 3
        for attempt in range(vision_retries):
            try:
                self.vision = StreamingVisionManager(
                    llm_manager=self.llm,
                    memory_manager=self.memory,
                    lava_model=getattr(_cfg(), 'LAVA_MODEL', 'llava:latest'),
                    camera_id=getattr(_cfg(), 'CAMERA_ID', 0),
                    target_fps=getattr(_cfg(), 'CAMERA_FPS', 5)
                )
                logger.info("✅ Vision initialized")
                break
            except Exception as e:
                logger.error(f"Vision init attempt {attempt+1} failed: {e}")
                if attempt < vision_retries - 1:
                    await asyncio.sleep(2)
                else:
                    self.vision = None

        # PersonaBridge starts the CognitiveOrganism before AppState creates
        # the vision manager. Attach here, after both objects exist; attempting
        # this during orchestrator construction silently skipped the wiring.
        self._wire_vision_to_cognition()

        self.audio      = None
        self.conv_audio = None

        # ── Wire Strategic Cognitive Engine ─────────────────────────────────
        try:
            from cognition.strategic_cognitive_engine import StrategicCognitiveEngine
            organism_ref = getattr(self.persona, '_organism', None) if self.persona else None
            if organism_ref:
                self.sce = StrategicCognitiveEngine(organism_ref)
                logger.info("♟️  StrategicCognitiveEngine wired")
            else:
                self.sce = None
        except Exception as _e:
            logger.warning(f"SCE init failed (non-fatal): {_e}")
            self.sce = None

        # ── Wire PandoraBOX Network ─────────────────────────────────────────────────
        try:
            _net_cfg = __import__('managers.settings_manager', fromlist=['config']).config
            _network_role = str(getattr(_net_cfg, 'LUMINA_NETWORK_ROLE', 'master') or 'master').strip().lower()
            if _network_role not in {'master', 'child', 'standalone'}:
                logger.warning("Unknown LUMINA_NETWORK_ROLE=%r; using standalone", _network_role)
                _network_role = 'standalone'
            if getattr(_net_cfg, 'LUMINA_NETWORK_ENABLED', False) and _network_role == 'master':
                from cognition.lumina_network import LuminaNetwork
                self.lumina_network = LuminaNetwork(
                    persona = self.persona,
                    llm     = self.llm,
                )
                _children_cfg = getattr(_net_cfg, 'LUMINA_CHILDREN', [])
                if _children_cfg:
                    self.lumina_network.load_from_config(_children_cfg)
                _master_name = getattr(_net_cfg, 'LUMINA_MASTER_NAME', 'PandoraBOX-Master')
                from core.lumina_network_config import master_callback_base_url
                _master_url = master_callback_base_url(_net_cfg)
                self.lumina_network.set_master_info(_master_url, _master_name)
                logger.info(f"🌐 LuminaNetwork ready — {len(_children_cfg)} child(ren)")
            else:
                self.lumina_network = None
                if _network_role == 'child':
                    logger.info("🌐 Lumina network role=child — accepts master requests; outbound peer network disabled")
                elif _network_role == 'standalone':
                    logger.info("🌐 Lumina network role=standalone — peer networking disabled")
        except Exception as _e:
            logger.warning(f"LuminaNetwork init failed (non-fatal): {_e}")
            self.lumina_network = None

        # ── Wire Abstract Reasoning Engine ────────────────────────────────────
        try:
            from cognition.abstract_reasoning_engine import AbstractReasoningEngine
            organism_ref = getattr(self.persona, '_organism', None) if self.persona else None
            if organism_ref:
                self.are = AbstractReasoningEngine(
                    organism = organism_ref,
                    llm      = self.llm,
                    memory   = self.memory,
                )
                logger.info("🧠 AbstractReasoningEngine wired")
            else:
                self.are = None
        except Exception as _e:
            logger.warning(f"ARE init failed (non-fatal): {_e}")
            self.are = None

        # ── Wire Active Cognitive Context (CAG Layer 2) ─────────────────────────
        try:
            from cognition.active_cognitive_context import ActiveCognitiveContext
            organism_ref = getattr(self.persona, '_organism', None) if self.persona else None
            if organism_ref:
                self.acc = ActiveCognitiveContext(organism=organism_ref, llm=self.llm)
                logger.info("🧠 ActiveCognitiveContext (CAG) wired")
            else:
                self.acc = None
        except Exception as _e:
            logger.warning(f"ACC init failed (non-fatal): {_e}")
            self.acc = None

        # ── Wire Empathy Engine ──────────────────────────────────────────────
        try:
            from cognition.empathy_engine import EmpathyEngine
            organism_ref = getattr(self.persona, '_organism', None) if self.persona else None
            rm_ref = getattr(organism_ref, 'relational_memory', None) if organism_ref else None
            if organism_ref:
                self.empathy_engine = EmpathyEngine(
                    organism          = organism_ref,
                    llm               = self.llm,
                    relational_memory = rm_ref,
                    multilingual_model_id = getattr(
                        _cfg(), "AFFECT_EMBEDDING_MODEL",
                        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                    ),
                )
                logger.info("❤️  EmpathyEngine wired")
            else:
                self.empathy_engine = None
        except Exception as _e:
            logger.warning(f"EmpathyEngine init failed (non-fatal): {_e}")
            self.empathy_engine = None

        # ── Wire social presence engine ──────────────────────────────────
        # Needs: vision manager + organism (from persona) + LLM
        # Called after all three are initialised so nothing is None-dependent.
        if self.vision is not None:
            organism = getattr(self.persona, '_organism', None) if self.persona else None

            def _tts_speak(text: str) -> None:
                """Push text to TTS — walk all available audio handles."""
                try:
                    try:
                        from core.interface_api import record_presence
                        record_presence(text)
                    except Exception:
                        pass
                    # FluidVoice / AudioManager both expose .speak(text)
                    for _handle in (
                        getattr(self, 'audio', None),
                        getattr(self, 'conv_audio', None),
                    ):
                        if _handle is None:
                            continue
                        # Try .speak() directly (FluidVoice, AudioManager)
                        if hasattr(_handle, 'speak'):
                            _handle.speak(text)
                            return
                        # Try .tts.speak() (some wrappers)
                        _tts = getattr(_handle, 'tts', None)
                        if _tts and hasattr(_tts, 'speak'):
                            _tts.speak(text)
                            return
                    logger.info(f"[PresenceEngine TTS] {text}")
                except Exception as _e:
                    logger.debug(f"PresenceEngine TTS: {_e}")

            try:
                self.vision.attach_presence_engine(
                    organism = organism,
                    llm      = self.llm,
                    tts_fn   = _tts_speak,
                )
            except Exception as _e:
                logger.error(f"PresenceEngine wire failed: {_e}")

        # Sensor-only mode keeps external occupancy available when the
        # camera manager/stream is disabled. It has no face identity and does
        # not generate speech by itself.
        _body_presence_enabled = bool(getattr(_cfg(), 'HOME_ASSISTANT_PRESENCE_ENABLED', False))
        try:
            _organism_for_body = getattr(self.persona, '_organism', None) if self.persona else None
            if _organism_for_body is not None:
                from cognition.body_runtime import get_body_runtime
                _body_presence_enabled = bool(get_body_runtime(_organism_for_body).config_value(
                    'HOME_ASSISTANT_PRESENCE_ENABLED', _body_presence_enabled
                ))
        except Exception:
            pass
        if self.vision is None and _body_presence_enabled:
            try:
                from cognition.presence_engine import PresenceEngine
                self.presence_engine = PresenceEngine(
                    organism=getattr(self.persona, '_organism', None) if self.persona else None,
                    llm=self.llm,
                )
                logger.info("✅ Sensor-only PresenceEngine attached")
            except Exception as _e:
                logger.warning("Sensor-only PresenceEngine unavailable (non-fatal): %s", _e)

        # Home Assistant polling belongs to the separately launched Body.
        # Reconcile only shuts down a legacy Brain-side monitor if one exists;
        # it never starts a second polling loop.
        try:
            organism = getattr(self.persona, '_organism', None) if self.persona else None
            if organism is not None:
                from cognition.universal_connector import get_universal_connector
                await get_universal_connector(organism).reconcile_home_assistant_monitor()
        except Exception as _e:
            logger.warning("Home Assistant monitor startup failed (non-fatal): %s", _e)

        # `ready` gates the Body bridge and must represent the conversational
        # Brain core, not merely successful construction of an LLM wrapper.
        self.ready = bool(
            self.llm
            and self.persona
            and getattr(self.persona, 'is_ready', False)
        )
        self.initializing = False
        if not self.ready:
            logger.error(
                "Brain initialization completed degraded: llm=%s persona=%s",
                self.llm is not None,
                bool(self.persona and getattr(self.persona, 'is_ready', False)),
            )

    def _wire_vision_to_cognition(self) -> bool:
        """Attach the Brain-PC vision manager to the live cognitive organism."""
        self._vision_attached_to_cognition = False
        if self.vision is None or self.persona is None:
            return False

        organism = getattr(self.persona, '_organism', None)
        if organism is None:
            return False

        loop = getattr(organism, '_loop', None)
        attach = getattr(loop, 'attach_vision', None)
        try:
            if callable(attach):
                attach(self.vision)
                self._vision_attached_to_cognition = True
            else:
                # Keep direct Brain-side access available even if a custom
                # organism implementation has no ambient-thought loop hook.
                organism._vision_manager = self.vision
                self._vision_attached_to_cognition = True
        except Exception:
            logger.exception("Brain-PC vision attachment to cognition failed")
            return False

        if self._vision_attached_to_cognition:
            logger.info("Brain-PC vision manager attached to cognitive organism")
        return self._vision_attached_to_cognition

    def brain_workflow_status(self) -> dict:
        """Return an observational snapshot of the Brain's own workflow."""
        persona = self.persona
        organism = getattr(persona, '_organism', None) if persona else None
        loop = getattr(organism, '_loop', None) if organism else None
        loop_thread = getattr(loop, '_thread', None) if loop else None
        workspace = getattr(organism, 'workspace', None) if organism else None
        loop_modules = {}
        if loop is not None:
            for module_name in (
                '_tte', '_cde', '_dts', '_mte', '_naw', '_phase1', '_phase2',
                '_resource_economy', '_goal_quality_filter', '_long_horizon_planner',
                '_autonomous_reflection', '_auto_experiment', '_cognitive_audit',
                '_cognitive_immune', '_flux_engine', '_attention_engine',
            ):
                loop_modules[module_name.lstrip('_')] = getattr(loop, module_name, None) is not None
        orchestrator_task = getattr(self.orchestrator, '_task', None)
        orchestrator_task_alive = bool(
            orchestrator_task is not None
            and not orchestrator_task.done()
        )
        return {
            'ready': bool(self.ready and persona and getattr(persona, 'is_ready', False)),
            'initializing': bool(self.initializing),
            'response_pipeline': 'PersonaBridge.get_response_stream',
            'components': {
                'llm': {'available': self.llm is not None},
                'persona_bridge': {
                    'available': persona is not None,
                    'ready': bool(persona and getattr(persona, 'is_ready', False)),
                    'chat_stage': getattr(persona, '_chat_stage', 'idle') if persona else 'unavailable',
                    'last_turn': persona.get_last_turn_trace() if persona and hasattr(persona, 'get_last_turn_trace') else None,
                    'goal_means': persona.get_goal_means_status() if persona and hasattr(persona, 'get_goal_means_status') else None,
                },
                'cognitive_organism': {
                    'available': organism is not None,
                    'initialized_modules': {
                        name: getattr(organism, name, None) is not None
                        for name in ('energy', 'attention', 'curiosity', 'goal_ecology',
                                     'arbitration', 'meta_cognition', 'workspace', 'semantic_memory')
                    } if organism is not None else {},
                },
                'internal_thought_loop': {
                    'available': loop is not None,
                    'running': bool(getattr(loop, '_running', False)),
                    'thread_alive': bool(loop_thread and loop_thread.is_alive()),
                    'slow_cycles': getattr(loop, '_slow_cycle_count', None),
                    'last_fast_cycle_at': getattr(loop, '_last_fast_cycle_at', None),
                    'fast_cycle_errors': getattr(loop, '_fast_cycle_error_count', None),
                    'last_slow_cycle_at': getattr(loop, '_last_slow_cycle_at', None),
                    'slow_cycle_errors': getattr(loop, '_slow_cycle_error_count', None),
                    'last_slow_cycle_error_type': getattr(loop, '_last_slow_cycle_error_type', None),
                    'initialized_modules': loop_modules,
                    'module_ticks': (
                        loop.module_tick_snapshot()
                        if loop is not None and callable(getattr(loop, 'module_tick_snapshot', None))
                        else {}
                    ),
                    'module_tick_analysis': (
                        loop.module_tick_analysis()
                        if loop is not None and callable(getattr(loop, 'module_tick_analysis', None))
                        else None
                    ),
                },
                'global_workspace': {'available': workspace is not None},
                'memory': {'available': self.memory is not None},
                'brain_pc_vision': {
                    'manager_available': self.vision is not None,
                    'camera_active': bool(getattr(self.vision, 'camera_active', False)) if self.vision else False,
                    'attached_to_cognition': self._vision_attached_to_cognition,
                },
                'autonomous_orchestrator': {
                    'available': self.orchestrator is not None,
                    # The flag can remain true after an unhandled exception
                    # terminates _run(). Report effective runtime health, not
                    # only the requested lifecycle state.
                    'running': bool(
                        getattr(self.orchestrator, '_running', False)
                        and orchestrator_task_alive
                    ),
                    'requested_running': bool(getattr(self.orchestrator, '_running', False)),
                    'task_alive': orchestrator_task_alive,
                    'cycles': getattr(self.orchestrator, '_cycle_count', None),
                    'last_cycle_at': getattr(self.orchestrator, '_last_cycle_at', None),
                    'cycle_errors': getattr(self.orchestrator, '_cycle_error_count', None),
                    'last_cycle_error_type': getattr(self.orchestrator, '_last_cycle_error_type', None),
                },
            },
        }

    def notify_user_turn(self, text: str, user_id: str = "default") -> bool:
        """Feed an accepted human turn to the autonomous cognitive loop once.

        Call this at user-input boundaries after validation/sanitization. Peer
        dialogue and internally generated/proactive turns must use their own
        pathways and must not be represented as human input here.
        """
        text = str(text or "").strip()
        if not text or self.orchestrator is None:
            return False
        try:
            self.orchestrator.notify_user_message(text, user_id)
            return True
        except Exception:
            logger.exception("Accepted user turn could not be queued for the orchestrator")
            return False

    def schedule_deferred_cognitive_stages(
        self, user_text: str, assistant_text: str, user_id: str = "default",
        reflection_epoch: int = 0, turn_id: str = "", cognitive_scope_id: str = "",
    ) -> bool:
        """Schedule bounded post-answer analysis without delaying chat delivery."""
        persona = self.persona
        if persona is None or not assistant_text:
            return False
        deferred = getattr(persona, "run_deferred_analysis", None)
        goal_means = getattr(persona, "run_deferred_goal_means_analysis", None)
        if not callable(deferred) and not callable(goal_means):
            return False
        try:
            trace = persona.get_last_turn_trace() if callable(
                getattr(persona, "get_last_turn_trace", None)
            ) else {}
            if not isinstance(trace, dict):
                trace = {}
            turn_id = str(turn_id or trace.get("turn_id") or "")
            cognitive_scope_id = str(
                cognitive_scope_id or trace.get("cognitive_scope_id") or user_id
            )
        except Exception:
            turn_id = ""
        record_stage = getattr(persona, "record_deferred_turn_stage", None)

        def record(stage_name: str, status: str, detail: str = "") -> None:
            if turn_id and callable(record_stage):
                record_stage(turn_id, stage_name, status, detail)

        def run_stages():
            if callable(deferred):
                try:
                    result = deferred(user_text, assistant_text, user_id, reflection_epoch)
                    result_status = str(result or "unavailable")
                    record("continuity_analysis_post_response", result_status)
                except Exception:
                    record("continuity_analysis_post_response", "failed")
                    logger.exception("Deferred continuity analysis failed")
            else:
                record("continuity_analysis_post_response", "skipped_unavailable")
            if callable(goal_means):
                try:
                    result = goal_means(user_text, user_id, user_id, cognitive_scope_id)
                    result_status = (
                        str(result.get("status") or "failed")
                        if isinstance(result, dict) else "failed"
                    )
                    record("goal_means_post_response", result_status)
                except Exception:
                    record("goal_means_post_response", "failed")
                    logger.exception("Deferred goal-means analysis failed")
            else:
                record("goal_means_post_response", "skipped_unavailable")

        record("continuity_analysis_post_response", "scheduled")
        record("goal_means_post_response", "scheduled")

        try:
            task = asyncio.create_task(asyncio.to_thread(run_stages))
        except RuntimeError:
            record("continuity_analysis_post_response", "failed", "no_running_event_loop")
            record("goal_means_post_response", "failed", "no_running_event_loop")
            logger.warning("Deferred cognitive stages were not scheduled: no running event loop")
            return False
        self._deferred_cognitive_tasks.add(task)

        def finish(done_task):
            self._deferred_cognitive_tasks.discard(done_task)
            if not done_task.cancelled() and done_task.exception() is not None:
                logger.error("Deferred cognitive stages failed: %s", done_task.exception())

        task.add_done_callback(finish)
        return True

    def ensure_audio_ready(self) -> bool:
        if self.audio:
            return True
        try:
            self.audio = create_audio_manager()
            self.conv_audio = ConversationalAudioManager(self.audio, self.tts_stop_event)
            self.conv_audio._vision_ref = self.vision
            logger.info("✅ Audio ready (lazy init)")
            return True
        except Exception as e:
            logger.error(f"Audio init failed: {e}")
            self.audio = None
            self.conv_audio = None
            return False

    def reload_audio(self, force: bool = False):
        """
        Reload AudioManager only when TTS/STT provider actually changed.
        VAD settings, voice reference, and other hot-swappable params are
        applied directly without a full reload to avoid the 7s XTTS reload.
        Pass force=True to always reload (e.g. first init).
        """
        cfg = self._refresh_config()

        if self.audio is None:
            return

        # Apply hot-swappable settings directly — no reload needed
        if self.conv_audio:
            self.conv_audio.set_aggressiveness(cfg.VAD_AGGRESSIVENESS)
            self.conv_audio.speech_onset_chunks = cfg.VAD_ONSET_CHUNKS
            self.conv_audio.silence_duration    = cfg.VAD_SILENCE_DURATION
            self.conv_audio.min_speech_duration = cfg.VAD_MIN_SPEECH_DURATION
            self.conv_audio.energy_gate_factor  = cfg.VAD_ENERGY_GATE_FACTOR
            self.conv_audio.tts_post_roll_ms    = getattr(cfg, 'TTS_POST_ROLL_MS', 250)
            logger.info("✅ VAD settings applied (no reload)")

        # Only reload the heavy audio stack if TTS/STT provider changed
        def _canonical_tts(provider):
            return 'edge_tts' if provider == 'edge' else provider

        current_tts = self.audio.tts_engine.get('type') if self.audio.tts_engine else None
        current_stt = self.audio.stt_engine.get('type') if self.audio.stt_engine else None
        tts_changed = current_tts != _canonical_tts(cfg.TTS_PROVIDER)
        stt_changed = current_stt != cfg.STT_PROVIDER

        if not force and not tts_changed and not stt_changed:
            # Hot-swap voice reference if it changed
            if self.audio.tts_engine and cfg.COQUI_VOICE_REFERENCE:
                self.audio.update_voice_reference(cfg.COQUI_VOICE_REFERENCE)
            # Hot-swap language if it changed (Coqui only)
            if self.audio.tts_engine and self.audio.tts_engine.get('type') == 'coqui':
                self.audio.update_language(cfg.VOICE_LANGUAGE)
            logger.info("✅ Audio settings applied (no model reload needed)")
            return

        try:
            logger.info(f"Reloading audio (TTS changed={tts_changed}, STT changed={stt_changed})")
            if self.conv_audio and self.conv_audio.is_listening:
                self.conv_audio.stop_conversation()
            # Explicitly tear down Coqui/PyTorch before initialising the new
            # provider — prevents heap corruption when switching Coqui → pyttsx3
            if self.audio is not None:
                try:
                    self.audio.teardown()
                except Exception as _te:
                    logger.debug(f"Audio teardown warning (non-fatal): {_te}")
                self.audio = None
                self.conv_audio = None
            self.audio = create_audio_manager()
            if self.audio:
                self.conv_audio = ConversationalAudioManager(self.audio, self.tts_stop_event)
                self.conv_audio._vision_ref = self.vision
            logger.info("✅ Audio reloaded")
        except Exception as e:
            logger.error(f"Audio reload failed: {e}")

    def _refresh_config(self):
        """Reload config from JSON and update the module-level singleton.
        This is the single source of truth — no in-memory object sync needed."""
        fresh = load_settings()
        _settings_mod.config = fresh
        return fresh

    def reload_llm(self):
        cfg = self._refresh_config()
        try:
            # Save history BEFORE creating new LLMManager (which starts empty)
            from managers.session_manager import get_session_manager
            sess = get_session_manager()
            old_history = sess.save_before_reload(self.llm.history if self.llm else [])

            self.llm = create_llm_manager()

            # Restore history into the fresh LLMManager
            restored = sess.restore_after_reload(self.llm)
            # Give session manager a reference to the new LLM fn for compression
            sess.set_llm_fn(self.llm.generate_bare)

            # ── Rewire PersonaBridge so it uses the new LLM ────────────────
            # Without this, persona keeps calling the OLD provider even after
            # the user changes model/URL in settings.
            if self.persona is not None:
                new_bare   = getattr(self.llm, "generate_bare",   None) or getattr(self.llm, "generate", None)
                new_stream = getattr(self.llm, "generate_stream", None)
                # Swap the streaming fn used by the chat path
                self.persona._llm_stream_fn = new_stream
                # Goal-means analysis resolves its history-free interactive
                # method through this bound callable. Keep it on the same new
                # manager as the visible stream after an LLM settings reload.
                self.persona._external_llm_fn = new_bare
                # Swap the bare fn inside PandoraBOX's ExternalLLMAdapter
                try:
                    if new_bare and self.persona._system and self.persona._system.llm:
                        self.persona._system.llm._fn = new_bare
                        self.persona._system.llm.config.model_name = cfg.LLM_MODEL
                except Exception as _re:
                    logger.warning(f"Persona LLM adapter swap warning (non-fatal): {_re}")
                logger.info("✅ PersonaBridge LLM rewired to new provider")

            logger.info(f"✅ LLM reloaded: {cfg.LLM_PROVIDER}/{cfg.LLM_MODEL} ({restored} history turns restored)")
        except Exception as e:
            logger.error(f"LLM reload failed: {e}")

    def reload_memory(self):
        cfg = self._refresh_config()
        try:
            self.memory = create_memory_manager()
            logger.info(f"✅ Memory reloaded: {cfg.MEMORY_BACKEND}")
        except Exception as e:
            logger.error(f"Memory reload failed: {e}")

    def reload_vision(self):
        """Reload vision with new settings"""
        cfg = self._refresh_config()
        try:
            if self.vision:
                self.vision.cleanup()
            self.vision = StreamingVisionManager(
                llm_manager=self.llm,
                memory_manager=self.memory,
                lava_model=getattr(cfg, 'LAVA_MODEL', 'llava:latest'),
                camera_id=getattr(cfg, 'CAMERA_ID', 0),
                target_fps=getattr(cfg, 'CAMERA_FPS', 5)
            )
            self._wire_vision_to_cognition()
            logger.info("✅ Vision reloaded")
        except Exception as e:
            logger.error(f"Vision reload failed: {e}")
            self.vision = None
            self._wire_vision_to_cognition()

    def add_memory(self, content: str, role: str):
        if self.memory:
            try:
                self.memory.add_memory(content, {'role': role, 'timestamp': datetime.now().isoformat()})
            except Exception as e:
                logger.warning(f"Memory add failed: {e}")

    def get_context(self, query: str) -> str:
        if self.memory:
            try:
                return self.memory.get_context(query)
            except Exception as e:
                logger.warning(f"Memory get failed: {e}")
        return ""
    
    def get_uptime(self):
        """Get system uptime"""
        return time.time() - self.start_time


state = AppState()
