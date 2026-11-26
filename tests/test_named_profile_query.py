from cognition.profile_flow import (
    classify_memory_profile_intent,
    is_explicit_named_profile_query,
    render_explicit_profile_facts,
)


class _ProfileIntentEmbedder:
    model_name = "test-profile-intent"
    embedding_space_id = "test:text-embedding-nomic-embed-text-v1.5"

    def encode_interactive_with_metadata(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        rows = []
        for text in texts:
            normalized = text.casefold()
            if "explicitly stored in the named user profile" in normalized or \
                    "facts explicitly recorded in the user profile" in normalized or \
                    "profile facts that were explicitly saved" in normalized or \
                    "named user profile" in normalized or \
                    "explicitement enregistrées dans le profil utilisateur" in normalized or \
                    "faits sauvegardés dans mon profil" in normalized:
                rows.append([1.0, 0.0])
            elif any(marker in normalized for marker in (
                "earlier conversation", "previous conversations", "past conversations",
                "conversation memory", "conversations précédentes", "auparavant dans nos échanges",
                "previously say", "earlier statement", "préoccupation avais-je exprimée",
                "précédemment sur le rappel", "rappelle-moi ce que j'avais dit",
            )):
                rows.append([0.0, 1.0])
            elif "explain conceptually how a user profile" in normalized or \
                    "describe the general process" in normalized or \
                    "comment un profil utilisateur peut-il se construire" in normalized:
                rows.append([0.6, 0.6])
            elif "explain how user profiles are built" in normalized:
                rows.append([0.6, 0.6])
            else:
                rows.append([0.8, 0.2])
        return rows, self.embedding_space_id


def test_explicit_profile_read_queries_are_routed_but_profile_writes_are_not():
    embedder = _ProfileIntentEmbedder()
    assert is_explicit_named_profile_query(
        "Facts explicitly recorded in the user profile: what preference is saved?",
        embedder=embedder,
    )
    assert is_explicit_named_profile_query(
        "According to facts explicitly recorded in the user profile, what preferences are recorded?",
        embedder=embedder,
    )
    assert is_explicit_named_profile_query(
        "What preferences are stored in my named user profile?",
        embedder=embedder,
    )
    assert not is_explicit_named_profile_query(
        "From our previous conversations, what concern did I raise about memory recall and how my user profile is built?",
        embedder=embedder,
    )
    assert not is_explicit_named_profile_query(
        "Explain how user profiles are built from conversation exchanges.",
        embedder=embedder,
    )


def test_history_recall_intent_wins_over_profile_subject_in_prior_conversation_question():
    result = classify_memory_profile_intent(
        "From our previous conversations, what concern did I raise about memory recall and how my user profile is built?",
        embedder=_ProfileIntentEmbedder(),
    )

    assert result["intent"] == "history_recall"
    assert result["margin"] <= -0.04
    assert result["reason_code"] == "cross_lingual_semantic_centroid_margin"


def test_general_profile_concept_question_is_not_intercepted_as_history_recall():
    result = classify_memory_profile_intent(
        "Explain how user profiles are built from conversation exchanges.",
        embedder=_ProfileIntentEmbedder(),
    )

    assert result["intent"] == "uncertain"


def test_profile_answer_uses_only_supplied_provenance_backed_facts():
    rendered = render_explicit_profile_facts(
        [
            {"category": "preference", "value": "concise updates in French"},
            {"category": "interest", "value": "robotics"},
        ],
        "Quelle préférence est enregistrée dans mon profil ?",
    )

    assert rendered["status"] == "rendered_from_provenance_backed_profile"
    assert rendered["fact_count"] == 1
    assert rendered["categories"] == ["preference"]
    assert "concise updates in French" in rendered["answer"]
    assert "robotics" not in rendered["answer"]


def test_empty_profile_answer_does_not_fall_back_to_behavioral_inference():
    rendered = render_explicit_profile_facts(
        [], "What preference is stored in my profile?"
    )

    assert rendered["status"] == "empty"
    assert rendered["fact_count"] == 0
    assert "no provenance-backed explicit fact" in rendered["answer"]
