import json
from pathlib import Path

import pytest


def _load_dataset() -> list[dict]:
    path = Path(__file__).parent / 'nl_queries.jsonl'
    cases = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    assert len(cases) == 30, f'Golden dataset must have 30 entries, found {len(cases)}'

    categories: dict[str, list[dict]] = {}
    for c in cases:
        cat = c.get('category', 'unknown')
        categories.setdefault(cat, []).append(c)

    expected_categories = {
        'stock_level',
        'slow_moving',
        'supplier_lookup',
        'reorder_status',
        'demand_forecast',
    }
    assert set(categories.keys()) == expected_categories, (
        f'Expected categories {expected_categories}, got {set(categories.keys())}'
    )

    for cat, items in categories.items():
        assert len(items) == 6, f"Category '{cat}' has {len(items)} items, expected 6"

    for c in cases:
        assert c.get('id'), f"Missing 'id' in entry: {c}"
        assert c.get('category'), f"Missing 'category' in entry: {c['id']}"
        assert c.get('description'), f"Missing 'description' in entry: {c['id']}"
        assert c.get('nl_input'), f"Missing 'nl_input' in entry: {c['id']}"
        assert c.get('expected_action'), f"Missing 'expected_action' in entry: {c['id']}"
        assert 'expected_filters' in c, f"Missing 'expected_filters' in entry: {c['id']}"

    return cases


@pytest.fixture(scope='session')
def golden_dataset() -> list[dict]:
    return _load_dataset()
