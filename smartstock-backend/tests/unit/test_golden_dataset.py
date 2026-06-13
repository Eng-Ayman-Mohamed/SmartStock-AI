import json
from pathlib import Path


def test_golden_dataset_contains_30_annotated_queries():
    dataset_path = Path(__file__).resolve().parents[1] / 'golden_dataset' / 'nl_queries.jsonl'

    rows = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]

    assert len(rows) == 30
    assert all(row.get('query') for row in rows)
    assert all(row.get('expected_action') for row in rows)
    assert all('expected_filters' in row for row in rows)
