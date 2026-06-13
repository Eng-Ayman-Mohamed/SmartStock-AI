import json
from collections import Counter
from pathlib import Path


def test_golden_dataset_contains_30_annotated_queries():
    dataset_path = Path(__file__).resolve().parents[1] / 'golden_dataset' / 'nl_queries.jsonl'

    rows = [json.loads(line) for line in dataset_path.read_text().splitlines() if line.strip()]

    assert len(rows) == 30

    required_keys = {
        'id',
        'category',
        'nl_input',
        'expected_action',
        'expected_filters',
        'description',
    }
    for row in rows:
        assert required_keys.issubset(row.keys()), f'{row["id"]} missing keys'

    categories = Counter(row['category'] for row in rows)
    assert categories == {
        'stock_level_checks': 6,
        'slow_moving_items': 6,
        'supplier_lookup': 6,
        'reorder_status': 6,
        'demand_forecast': 6,
    }, f'Category distribution wrong: {dict(categories)}'
