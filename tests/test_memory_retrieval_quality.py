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
    faiss_l2_relevance,
    is_explicit_memory_recall_query,
    rank_documents,
    tokenize,
)


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

    def test_normalized_faiss_squared_l2_maps_to_cosine_relevance(self):
        # For unit vectors, d² = 2 - 2*cosine. These values are the exact
        # geometric mapping, not an arbitrary threshold for accepting recall.
        self.assertEqual(faiss_l2_relevance(0.0), 1.0)
        self.assertEqual(faiss_l2_relevance(1.0), 0.5)
        self.assertEqual(faiss_l2_relevance(2.0), 0.0)
        self.assertEqual(faiss_l2_relevance(3.0), 0.0)
        self.assertEqual(faiss_l2_relevance(float("inf")), 0.0)

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


if __name__ == "__main__":
    unittest.main()
