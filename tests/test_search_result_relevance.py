from unittest.mock import patch

from cognition.research_mcp import search_providers


def test_relevance_ranking_discards_grammar_match_on_question_word_only():
    results = [
        {
            "title": "Quelle ou quelles : règles de grammaire",
            "url": "https://example.net/grammar",
            "snippet": "Comment choisir la bonne forme dans une question française.",
            "content": "",
            "credibility": 0.88,
            "source": "bing_stealth",
        },
        {
            "title": "Functional affect and appraisal in cognitive systems",
            "url": "https://example.org/affect",
            "snippet": "A review of functional emotions, appraisal signals, and their causes.",
            "content": "",
            "credibility": 0.72,
            "source": "bing_stealth",
        },
    ]

    ranked = search_providers._rank_search_results(
        "Quelles émotions fonctionnelles sont actives selon les signaux internes et leur cause ?",
        results,
        3,
    )

    assert [item["url"] for item in ranked] == ["https://example.org/affect"]
    assert ranked[0]["relevance"] >= 0.20
    assert "credibility" in ranked[0]


def test_rank_score_prioritizes_relevance_over_domain_credibility():
    results = [
        {
            "title": "Curiosity",
            "url": "https://nature.com/curiosity",
            "snippet": "A brief unrelated mention of curiosity.",
            "credibility": 0.88,
            "source": "api",
        },
        {
            "title": "Radar target distance estimation",
            "url": "https://example.net/radar",
            "snippet": "Radar measures target distance and radial velocity in meters.",
            "credibility": 0.55,
            "source": "stealth",
        },
    ]

    ranked = search_providers._rank_search_results(
        "radar target distance and radial velocity", results, 2
    )

    assert [item["url"] for item in ranked] == ["https://example.net/radar"]


def test_auto_stealth_fallback_returns_only_relevant_candidates():
    relevant = {
        "title": "Radar target distance",
        "url": "https://example.net/radar",
        "snippet": "Target distance is measured in meters by the radar system.",
        "credibility": 0.55,
        "source": "bing_stealth",
    }
    irrelevant = {
        "title": "French question words",
        "url": "https://example.net/french",
        "snippet": "How to use quelle and quelles in grammar.",
        "credibility": 0.88,
        "source": "bing_stealth",
    }
    cfg = search_providers.SearchConfig(backend="auto", use_rss=True, use_stealth=True)

    with patch.object(search_providers, "_rss", return_value=[]), patch.object(
        search_providers, "_stealth", return_value=[irrelevant, relevant]
    ):
        ranked = search_providers.get_results("radar target distance", cfg=cfg, num=3)

    assert [item["url"] for item in ranked] == [relevant["url"]]
    assert ranked[0]["relevance"] > 0
