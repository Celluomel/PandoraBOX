import sys
import unittest
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
package = ModuleType("cognition")
package.__path__ = [str(ROOT / "cognition")]
sys.modules.setdefault("cognition", package)

from cognition.memory_retrieval import (
    exact_filename_recall_result,
    explicit_recall_abstention_result,
    explicit_recall_source_result,
    explicit_recall_search_term_groups,
    explicit_recall_source_result,
    filter_recall_lane_for_route,
    faiss_l2_relevance,
    is_explicit_memory_recall_query,
    rank_documents,
    semantic_user_recall_candidates,
    tokenize,
)
from cognition.profile_flow import (
    classify_memory_profile_intents,
    classify_memory_source_roles,
)


class _MemoryProfileRouterEmbedder:
    """Deterministic semantic-router fixture; production uses Nomic vectors."""

    model_name = "test-memory-profile-router"
    embedding_space_id = "test-memory-profile-router:text-embedding-nomic-embed-text-v1.5"

    def encode_interactive_with_metadata(self, texts):
        from cognition.profile_flow import (
            _GENERAL_MEMORY_PROFILE_EXAMPLES,
            _HISTORY_RECALL_EXAMPLES,
            _NO_EXPLICIT_UNCERTAINTY_EXAMPLES,
            _NO_CONTINUING_COMMITMENT_EXAMPLES,
            _PROFILE_LOOKUP_EXAMPLES,
            _PROFILE_FACT_SCOPE_EXAMPLES,
            _CONTINUING_COMMITMENT_EXAMPLES,
            _USER_UNCERTAINTY_EXAMPLES,
            _COMMUNICATIVE_POSTURE_EXAMPLES,
        )

        if isinstance(texts, str):
            texts = [texts]
        prototype_count = (
            len(_PROFILE_LOOKUP_EXAMPLES)
            + len(_HISTORY_RECALL_EXAMPLES)
            + len(_GENERAL_MEMORY_PROFILE_EXAMPLES)
        )
        category_count = sum(len(items) for items in _PROFILE_FACT_SCOPE_EXAMPLES.values())
        uncertainty_positive_start = prototype_count + category_count
        uncertainty_negative_start = uncertainty_positive_start + len(_USER_UNCERTAINTY_EXAMPLES)
        commitment_positive_start = uncertainty_negative_start + len(_NO_EXPLICIT_UNCERTAINTY_EXAMPLES)
        commitment_negative_start = commitment_positive_start + len(_CONTINUING_COMMITMENT_EXAMPLES)
        posture_start = commitment_negative_start + len(_NO_CONTINUING_COMMITMENT_EXAMPLES)
        query_start = posture_start + sum(
            len(examples) for examples in _COMMUNICATIVE_POSTURE_EXAMPLES.values()
        )
        batch_has_prototypes = len(texts) > query_start
        vectors = []
        for index, text in enumerate(texts):
            if not batch_has_prototypes:
                if any(marker in text.casefold() for marker in (
                    "i am committed", "keep pursuing this goal", "je m'engage",
                    "poursuivre ce projet", "quiero continuar este proyecto",
                    "ich möchte dieses vorhaben",
                )):
                    vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
                elif any(marker in text.casefold() for marker in (
                    "what uncertainties are you tracking", "quelles incertitudes",
                    "what goals are currently active", "quels objectifs sont actuellement actifs",
                    "explain how the system stores", "one-time question",
                )):
                    vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
                elif any(marker in text.casefold() for marker in (
                    "i am uncertain", "i do not know which", "cannot distinguish",
                    "je doute", "je ne sais pas encore", "no estoy seguro", "ich bin unsicher",
                )):
                    vectors.append([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
                elif any(marker in text.casefold() for marker in (
                    "previous conversations", "conversation précédente",
                )):
                    vectors.append([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                elif "explicitly stored" in text.casefold():
                    vectors.append([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
                elif "stance:challenging" in text.casefold():
                    vectors.append([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
                else:
                    vectors.append([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
                continue
            if index < len(_PROFILE_LOOKUP_EXAMPLES):
                vectors.append([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            elif index < len(_PROFILE_LOOKUP_EXAMPLES) + len(_HISTORY_RECALL_EXAMPLES):
                vectors.append([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            elif index < prototype_count:
                vectors.append([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
            elif index < uncertainty_positive_start:
                vectors.append([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
            elif index < uncertainty_negative_start:
                vectors.append([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
            elif index < commitment_positive_start:
                vectors.append([0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0])
            elif index < commitment_negative_start:
                vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
            elif index < posture_start:
                vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
            elif index < query_start:
                offset = posture_start
                for posture_index, examples in enumerate(_COMMUNICATIVE_POSTURE_EXAMPLES.values()):
                    end = offset + len(examples)
                    if index < end:
                        row = [0.0] * 7
                        row[posture_index] = 1.0
                        vectors.append(row)
                        break
                    offset = end
            elif "near-history-centroid" in text.casefold():
                vectors.append([0.0, 0.714, 0.700, 0.0, 0.0, 0.0, 0.0])
            elif "near-general-centroid" in text.casefold():
                vectors.append([0.0, 0.700, 0.714, 0.0, 0.0, 0.0, 0.0])
            elif any(marker in text.casefold() for marker in (
                "i am committed", "keep pursuing this goal", "je m'engage",
                "poursuivre ce projet", "quiero continuar este proyecto",
                "ich möchte dieses vorhaben",
            )):
                vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
            elif any(marker in text.casefold() for marker in (
                "what uncertainties are you tracking", "quelles incertitudes",
                "what goals are currently active", "quels objectifs sont actuellement actifs",
                "explain how the system stores", "one-time question",
            )):
                vectors.append([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
            elif any(marker in text.casefold() for marker in (
                "i am uncertain", "i do not know which", "cannot distinguish",
                "je doute", "je ne sais pas encore", "no estoy seguro", "ich bin unsicher",
            )):
                vectors.append([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
            elif any(marker in text.casefold() for marker in (
                "previous conversations", "conversation précédente",
            )):
                vectors.append([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            elif "explicitly stored" in text.casefold():
                vectors.append([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            elif "stance:challenging" in text.casefold():
                vectors.append([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0])
        return vectors, self.embedding_space_id


class _MemorySourceRoleEmbedder:
    """Independent deterministic fixture for source speech-act semantics."""

    model_name = "test-memory-source-role"
    embedding_space_id = "test-memory-source-role:text-embedding-nomic-embed-text-v1.5"

    def encode_interactive_with_metadata(self, texts):
        from cognition.profile_flow import (
            _HISTORICAL_RECALL_REQUEST_EXAMPLES,
            _USER_SOURCE_STATEMENT_EXAMPLES,
        )

        if isinstance(texts, str):
            texts = [texts]
        source_count = len(_USER_SOURCE_STATEMENT_EXAMPLES)
        request_count = len(_HISTORICAL_RECALL_REQUEST_EXAMPLES)
        vectors = []
        for index, text in enumerate(texts):
            if index < source_count:
                vectors.append([1.0, 0.0])
            elif index < source_count + request_count:
                vectors.append([0.0, 1.0])
            elif "uncertain role" in text.casefold():
                vectors.append([0.707, 0.707])
            elif "borderline source" in text.casefold():
                vectors.append([0.715, 0.697])
            elif "borderline uncertain" in text.casefold():
                vectors.append([0.712, 0.702])
            elif "source statement" in text.casefold():
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return vectors, self.embedding_space_id


class MemoryRetrievalQualityTests(unittest.TestCase):
    DOCUMENTS = [
        "The Arduino Q development board was considered for PandoraBOX's future physical body and embodiment, with a movable camera and LiDAR.",
        "The car wash is 150 metres from Fred's home; walking would leave the vehicle behind, so he needs to drive it there.",
        "LM Studio loaded Gemma as a vision model that accepts image inputs for camera analysis.",
        "The face recognition camera has known people including Nino, Theodore, Fred, and Marion.",
        "Coqui is the selected text to speech provider, and its voice file must be selected in voice settings.",
        "Flux and PandoraBOX exchange messages through the network dialogue session.",
        "A cake needs to be placed in a preheated oven to bake properly.",
        "The cognitive dashboard shows planning, memory, and affect telemetry for the organism.",
        "Fred doit conduire sa voiture jusqu'au lavage auto ; à pied, il laisserait le véhicule chez lui.",
        "LM Studio a chargé Gemma, un modèle de vision capable de traiter les images.",
        "Le fournisseur Coqui doit utiliser le fichier de voix sélectionné dans les paramètres audio.",
    ]

    CASES = [
        ("Which development board was considered for PandoraBOX's physical embodiment?", 0),
        ("Why must Fred drive rather than walk to clean the vehicle?", 1),
        ("What computer vision model was loaded in LM Studio?", 2),
        ("Which familiar person does the face tracker know named Nino?", 3),
        ("Which speech provider needs its voice file selected?", 4),
        ("How do Flux and PandoraBOX exchange messages?", 5),
        ("Pourquoi Fred doit-il conduire sa voiture au lavage auto ?", 8),
        ("Quel modèle de vision est chargé dans LM Studio ?", 9),
        ("Quel fournisseur vocal utilise le fichier de voix sélectionné ?", 10),
    ]

    def test_bilingual_retrieval_benchmark_recall_and_rank(self):
        reciprocal_ranks = []
        recall_at_three = 0
        for query, expected_index in self.CASES:
            ranked = rank_documents(query, self.DOCUMENTS, limit=3)
            indices = [index for index, _ in ranked]
            if expected_index in indices:
                recall_at_three += 1
                reciprocal_ranks.append(1.0 / (indices.index(expected_index) + 1))
            else:
                reciprocal_ranks.append(0.0)

        self.assertEqual(recall_at_three, len(self.CASES))
        self.assertGreaterEqual(sum(reciprocal_ranks) / len(reciprocal_ranks), 0.8)

    def test_french_accents_are_normalized_and_empty_queries_return_nothing(self):
        self.assertEqual(tokenize("Épuisé, déjà, à côté"), ["epuise", "deja", "cote"])
        self.assertEqual(rank_documents("le et ou", self.DOCUMENTS), [])

    def test_explicit_recall_sql_terms_are_bounded_and_keep_accent_variants(self):
        groups = explicit_recall_search_term_groups(
            "Quelle valeur du capteur était indiquée précédemment ?"
        )
        self.assertLessEqual(len(groups), 12)
        self.assertIn(("capteur",), groups)
        self.assertIn(("précédemment", "precedemment"), groups)

    def test_normalized_faiss_squared_l2_maps_to_cosine_relevance(self):
        # For unit vectors, d² = 2 - 2*cosine. These values are the exact
        # geometric mapping, not an arbitrary threshold for accepting recall.
        self.assertEqual(faiss_l2_relevance(0.0), 1.0)
        self.assertEqual(faiss_l2_relevance(1.0), 0.5)
        self.assertEqual(faiss_l2_relevance(2.0), 0.0)
        self.assertEqual(faiss_l2_relevance(3.0), 0.0)
        self.assertEqual(faiss_l2_relevance(float("inf")), 0.0)

    def test_semantic_historical_intent_selects_a_strong_user_source_verbatim(self):
        query = (
            "From earlier conversations, what concern did I raise about memory recall "
            "and how my user profile is built?"
        )
        result = explicit_recall_source_result(query, [{
            "id": "source-1", "memory_type": "user_message", "relevance": 0.91,
            "text": "User message: I have a concern about memory recall and how my user profile is built from exchanges.",
        }], explicit_intent=True)

        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertEqual(result["relevance"], 0.91)
        self.assertIn("I have a concern about memory recall", result["answer"])

    def test_semantic_recall_candidates_preserve_faiss_rank_and_user_provenance(self):
        query = "From earlier conversations, what concern did I raise about memory recall and my profile?"
        def classify_fixture_sources(texts):
            return [
                {"role": "historical_retrieval_request", "status": "classified"}
                if "From earlier conversations" in text else
                {"role": "user_source_statement", "status": "classified"}
                for text in texts
            ]

        candidates = semantic_user_recall_candidates([
            {"id": "assistant", "memory_type": "assistant_message", "relevance": 0.99,
             "text": "An assistant answer about memory."},
            {"id": "prior-recall", "memory_type": "user_message", "relevance": 0.99,
             "text": "User message: From earlier conversations, what concern did I raise about memory recall?"},
            {"id": "source", "memory_type": "user_message", "relevance": 0.91,
             "text": "User message: I worry about whether memory recall works and how my profile learns from exchanges."},
            {"id": "current", "memory_type": "user_message", "relevance": 1.0,
             "text": f"User message: {query}"},
        ], query, source_role_classifier=classify_fixture_sources)

        self.assertEqual([item["id"] for item in candidates], ["source"])
        answer = explicit_recall_source_result(query, candidates, explicit_intent=True)
        self.assertEqual(answer["status"], "supported_verbatim_source")
        self.assertEqual(answer["source_type"], "user_message")
        self.assertIn("I worry about whether memory recall works", answer["answer"])

    def test_semantic_recall_lane_does_not_apply_lexical_prefilter(self):
        query = (
            "Quelles explications ai-je laissées ouvertes dans mon message utilisateur "
            "où je doutais que le rappel mémoire de la dernière étape ait retrouvé la bonne source ? "
            "Réponds uniquement avec cette source utilisateur, ou indique que tu ne la retrouves pas."
        )
        source = {
            "id": 10096,
            "memory_type": "user_message",
            "relevance": 0.91,
            "text": (
                "User message: Je doute que le rappel mémoire de la dernière étape ait retrouvé "
                "la bonne source. Plusieurs explications restent possibles : l’index peut avoir "
                "renvoyé un souvenir inadéquat, le routage peut avoir sélectionné le mauvais "
                "contexte, ou l’introspection peut avoir mal interprété le souvenir."
            ),
        }

        self.assertEqual(filter_recall_lane_for_route([source], query, semantic_recall=True), [source])
        self.assertEqual(filter_recall_lane_for_route([source], query, semantic_recall=False), [])

        candidates = semantic_user_recall_candidates(
            [source], query,
            source_role_classifier=lambda texts: [{
                "status": "classified",
                "role": "user_source_statement",
            } for _ in texts],
        )
        result = explicit_recall_source_result(query, candidates, explicit_intent=True)
        self.assertEqual(result["status"], "supported_verbatim_source")
        self.assertIn("Plusieurs explications restent possibles", result["answer"])

    def test_source_role_router_distinguishes_statement_request_and_uncertainty(self):
        embedder = _MemorySourceRoleEmbedder()
        embedder.embedding_space_id = (
            "test-memory-source-role:isolated:text-embedding-nomic-embed-text-v1.5"
        )
        results = classify_memory_source_roles([
            "source statement: I doubt the previous memory result found the right source.",
            "historical request: What concern did I raise in the earlier conversation?",
            "uncertain role between a statement and a retrieval request",
            "borderline source with a small positive semantic margin",
            "borderline uncertain with a margin below the decision boundary",
        ], embedder=embedder)

        self.assertEqual(
            [result["role"] for result in results],
            [
                "user_source_statement", "historical_retrieval_request", "uncertain",
                "user_source_statement", "uncertain",
            ],
        )
        self.assertEqual(results[0]["score_semantics"],
                         "uncalibrated Nomic v1.5 cosine similarity; not a probability")

    def test_semantic_memory_profile_router_batches_source_questions(self):
        results = classify_memory_profile_intents([
            "From our previous conversations, what concern did I raise about your memory recall and how my user profile is built? Answer only from accessible conversation or memory evidence; if no supporting history is available, say so.",
            "I have a concern about whether memory recall works and how my user profile is built from exchanges.",
            "What facts are explicitly stored in my profile?",
        ], embedder=_MemoryProfileRouterEmbedder())

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["intent"], "history_recall")
        self.assertEqual(results[1]["intent"], "uncertain")
        self.assertEqual(results[2]["intent"], "profile_lookup")

    def test_history_router_uses_relative_semantic_winner_near_margin(self):
        embedder = _MemoryProfileRouterEmbedder()
        embedder.embedding_space_id = (
            "test-memory-profile-router:near-margin:text-embedding-nomic-embed-text-v1.5"
        )
        history, general = classify_memory_profile_intents([
            "near-history-centroid",
            "near-general-centroid",
        ], embedder=embedder)

        self.assertEqual(history["intent"], "history_recall")
        self.assertGreaterEqual(
            history["history_similarity"] - history["general_similarity"], 0.005,
        )
        self.assertEqual(general["intent"], "uncertain")

    def test_semantic_uncertainty_router_is_independent_of_memory_recall_route(self):
        results = classify_memory_profile_intents([
            "Je ne sais pas encore laquelle de ces sources est correcte, les éléments ne permettent pas de trancher.",
            "Quels éléments ai-je mentionnés dans notre conversation précédente ?",
        ], embedder=_MemoryProfileRouterEmbedder())

        self.assertTrue(results[0]["uncertainty_signal_candidate"])
        self.assertFalse(results[1]["uncertainty_signal_candidate"])
        self.assertEqual(results[1]["intent"], "history_recall")

    def test_continuing_commitment_router_distinguishes_commitment_from_question(self):
        results = classify_memory_profile_intents([
            "I am committed to continuing this project across future conversations; keep this as an ongoing objective.",
            "What uncertainties are you tracking in the Global Workspace?",
            "Je m'engage à continuer ce travail et à revenir sur cet objectif dans nos prochaines conversations.",
        ], embedder=_MemoryProfileRouterEmbedder())

        self.assertTrue(results[0]["continuing_commitment_candidate"])
        self.assertFalse(results[1]["continuing_commitment_candidate"])
        self.assertTrue(results[2]["continuing_commitment_candidate"])
        self.assertEqual(
            results[1]["commitment_router_reason"],
            "below_commitment_signal_threshold",
        )

    def test_communicative_posture_is_semantic_and_scores_are_uncalibrated(self):
        results = classify_memory_profile_intents(
            ["stance:challenging", "near-general-centroid"],
            embedder=_MemoryProfileRouterEmbedder(),
        )
        result = results[0]["communicative_posture"]

        self.assertEqual(result["status"], "classified")
        self.assertEqual(result["stance"], "challenging")
        self.assertEqual(result["source"], "cross_lingual_semantic_centroid")
        self.assertIn("not a probability", result["score_semantics"])
        self.assertEqual(results[1]["communicative_posture"]["status"], "uncertain")

    def test_semantic_historical_intent_abstains_without_a_clear_retrieved_source(self):
        query = "From earlier conversations, what concern did I raise about memory recall?"
        result = explicit_recall_abstention_result(query, [{
            "id": "weak-source", "memory_type": "user_message", "relevance": 0.63,
            "text": "User message: I asked about an unrelated software setting.",
        }], explicit_intent=True)

        self.assertEqual(result["status"], "abstained_no_relevant_source")
        self.assertIsNone(result["source_ref"])
        self.assertIn("couldn't find", result["answer"])

    def test_exact_filename_recall_extracts_user_authored_source_not_answer_guess(self):
        result = exact_filename_recall_result(
            "What do you remember about the markdown status file I asked you to create "
            "for the cognitive harness audit? Give only its filename.",
            [
                {
                    "id": 21,
                    "memory_type": "episodic",
                    "text": (
                        "Conversation — User: /C:/work/docs/COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md "
                        "| Lumina: I think the file was markdown_status_audit.md"
                    ),
                    "relevance": 0.88,
                },
            ],
        )

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["answer"], "`COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md`")
        self.assertEqual(result["source_type"], "episodic")

    def test_exact_filename_recall_abstains_when_only_assistant_claim_has_filename(self):
        result = exact_filename_recall_result(
            "What do you remember about the markdown status file I asked you to create "
            "for the cognitive harness audit? Give only its filename.",
            [
                {
                    "id": 22,
                    "memory_type": "episodic",
                    "text": (
                        "Conversation — User: Did we discuss the cognitive harness audit? "
                        "| Lumina: The file was markdown_status_audit.md"
                    ),
                    "relevance": 0.99,
                },
            ],
        )

        self.assertEqual(result["status"], "abstained_no_source")
        self.assertIsNone(result["source_ref"])

    def test_exact_filename_recall_supports_french_request_and_ignores_non_recall(self):
        source = {
            "id": 23,
            "memory_type": "user_message",
            "text": "User message: /C:/work/docs/rapport-audit.md",
            "relevance": 0.91,
        }
        result = exact_filename_recall_result(
            "Tu te rappelles du nom du fichier demandé pour l'audit ?", [source],
        )

        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["answer"], "`rapport-audit.md`")
        self.assertIsNone(exact_filename_recall_result("What filename is this?", [source]))

    def test_direct_filename_lookup_uses_grounded_recall_without_remember_wording(self):
        query = (
            "Quel est le nom du fichier Markdown qui contient le statut de l’audit cognitif ? "
            "Réponds uniquement par le nom du fichier."
        )
        self.assertTrue(is_explicit_memory_recall_query(query))
        result = exact_filename_recall_result(query, [{
            "id": 24,
            "memory_type": "user_message",
            "text": "User message: /docs/COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md",
            "relevance": 0.89,
        }])
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["answer"], "`COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md`")

    def test_filename_lookup_phrase_is_not_inferred_from_bare_filename_reference(self):
        self.assertFalse(is_explicit_memory_recall_query("What filename is this?"))

    def test_markdown_filename_question_is_routed_to_grounded_recall(self):
        query = (
            "What is the Markdown filename containing the cognitive audit status? "
            "Answer only with the filename."
        )
        self.assertTrue(is_explicit_memory_recall_query(query))
        result = exact_filename_recall_result(query, [{
            "id": 25,
            "memory_type": "user_message",
            "text": "User message: docs/COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md",
            "relevance": 0.89,
        }])
        self.assertEqual(result["status"], "supported")
        self.assertEqual(result["answer"], "`COGNITIVE_HARNESS_AUDIT_STATUS_2026-11-11.md`")

    def test_filename_recall_does_not_promote_prose_fragment_to_filename(self):
        query = "What is the filename containing the answer.my phrase in my note?"
        result = exact_filename_recall_result(query, [{
            "id": 26,
            "memory_type": "user_message",
            "text": "User message: In my note, the phrase answer.my is prose, not a file.",
            "relevance": 0.86,
        }])
        self.assertEqual(result["status"], "abstained_no_source")
        self.assertIsNone(result["source_ref"])


if __name__ == "__main__":
    unittest.main()
