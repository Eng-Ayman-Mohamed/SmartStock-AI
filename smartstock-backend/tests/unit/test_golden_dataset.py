import json
from pathlib import Path


def test_golden_dataset_contains_30_annotated_queries():
    dataset_path = Path(__file__).resolve().parents[1] / 'golden_dataset' / 'nl_queries.jsonl'

    rows = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]

    assert len(rows) == 30
    assert all(row.get('nl_input') for row in rows)
    assert all(row.get('expected_action') for row in rows)
    assert all('expected_filters' in row for row in rows)
    assert all(row.get('category') for row in rows)
    assert all(row.get('description') for row in rows)

    categories = {}
    for row in rows:
        categories.setdefault(row['category'], []).append(row)
    for cat, items in categories.items():
        assert len(items) == 6, f"Category '{cat}' has {len(items)} items, expected 6"
