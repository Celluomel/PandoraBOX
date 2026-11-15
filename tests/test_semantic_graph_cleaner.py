import sqlite3

from cognition.semantic_graph_cleaner import SemanticGraphCleaner


def _graph_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE concepts (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE relations (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            rel_type TEXT NOT NULL,
            weight REAL NOT NULL,
            last_used REAL NOT NULL,
            UNIQUE(source_id, target_id, rel_type)
        );
        """
    )
    return conn


def test_relation_enrichment_merges_duplicate_semantic_edge_without_integrity_error():
    conn = _graph_connection()
    conn.executemany(
        "INSERT INTO concepts (id, name) VALUES (?, ?)",
        [(1, "goal"), (2, "purpose")],
    )
    conn.executemany(
        """INSERT INTO relations
           (id, source_id, target_id, rel_type, weight, last_used)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (1, 1, 2, "goal_link", 0.4, 10.0),
            (2, 1, 2, "related_to", 0.8, 20.0),
        ],
    )

    enriched = SemanticGraphCleaner()._enrich_relation_types(conn)

    rows = conn.execute(
        "SELECT rel_type, weight, last_used FROM relations WHERE source_id=1 AND target_id=2"
    ).fetchall()
    assert enriched == 1
    assert len(rows) == 1
    assert rows[0]["rel_type"] == "goal_link"
    assert rows[0]["weight"] == 0.8
    assert rows[0]["last_used"] == 20.0
    conn.close()


def test_relation_enrichment_retypes_when_target_edge_does_not_exist():
    conn = _graph_connection()
    conn.executemany(
        "INSERT INTO concepts (id, name) VALUES (?, ?)",
        [(1, "identity"), (2, "principle")],
    )
    conn.execute(
        """INSERT INTO relations
           (id, source_id, target_id, rel_type, weight, last_used)
           VALUES (1, 1, 2, 'related_to', 0.6, 12.0)"""
    )

    enriched = SemanticGraphCleaner()._enrich_relation_types(conn)

    row = conn.execute("SELECT rel_type FROM relations WHERE id=1").fetchone()
    assert enriched == 1
    assert row["rel_type"] == "identity_link"
    conn.close()
