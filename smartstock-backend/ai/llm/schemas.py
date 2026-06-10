from enum import Enum
from typing import Optional, List, Dict, Any


class NLQueryAction(str, Enum):
    GET_INVENTORY    = "get_inventory"
    GET_SALES_REPORT = "get_sales_report"
    GET_LOW_STOCK    = "get_low_stock"
    FORECAST_DEMAND  = "forecast_demand"
    GET_SUPPLIER_INFO = "get_supplier_info"
    GET_TOTAL_VALUE  = "get_total_value"
    GET_TOP_PRODUCTS = "get_top_products"


# ── Allowed fields per action (for validation) ────────────────────────────────

ACTION_ALLOWED_FIELDS: Dict[str, List[str]] = {
    "get_inventory": [
        "product_name", "sku_code", "category", "supplier_name",
        "quantity_on_hand", "quantity_available", "is_active",
    ],
    "get_sales_report": [
        "sku_code", "product_name", "date_from", "date_to",
        "quantity_sold",
    ],
    "get_low_stock": [
        "product_name", "sku_code", "category",
        "quantity_on_hand", "reorder_point",
    ],
    "forecast_demand": [
        "product_name", "sku_code",
    ],
    "get_supplier_info": [
        "supplier_name", "contact_email", "is_active",
    ],
    "get_total_value": [
        "product_name", "category", "supplier_name", "is_active",
    ],
    "get_top_products": [
        "category", "date_from", "date_to", "limit",
    ],
}

VALID_OPERATORS = [
    "eq", "neq", "lt", "lte", "gt", "gte",
    "contains", "starts_with", "ends_with", "in", "not_in",
]


class Condition:
    """A single filter condition: {field, op, value}."""

    def __init__(self, field: str, op: str, value: Any):
        self.field = field
        self.op = op
        self.value = value

    def to_dict(self) -> dict:
        return {"field": self.field, "op": self.op, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Condition":
        return cls(field=data["field"], op=data["op"], value=data["value"])


class NLQueryFilters:
    """
    Conditions-based container for filter values extracted from the user's NL query.
    Supports conditions array plus sort/limit/offset.
    """

    def __init__(
        self,
        conditions: Optional[List[Condition]] = None,
        sort: Optional[str] = None,
        sort_order: Optional[str] = "asc",
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        self.conditions = conditions or []
        self.sort = sort
        self.sort_order = sort_order or "asc"
        self.limit = limit
        self.offset = offset

    def to_dict(self) -> dict:
        d = {}
        if self.conditions:
            d["conditions"] = [c.to_dict() for c in self.conditions]
        if self.sort:
            d["sort"] = self.sort
            d["sort_order"] = self.sort_order
        if self.limit is not None:
            d["limit"] = self.limit
        if self.offset is not None:
            d["offset"] = self.offset
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "NLQueryFilters":
        raw_conditions = data.get("conditions", [])
        conditions = [Condition.from_dict(c) for c in raw_conditions]
        return cls(
            conditions=conditions,
            sort=data.get("sort"),
            sort_order=data.get("sort_order", "asc"),
            limit=data.get("limit"),
            offset=data.get("offset"),
        )


class NLQueryResult:
    def __init__(self, action: NLQueryAction, filters: NLQueryFilters):
        self.action = action
        self.filters = filters

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "filters": self.filters.to_dict(),
        }


# ── JSON Schema for GPT-4o structured output ─────────────────────────────────

NL_QUERY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [a.value for a in NLQueryAction],
            "description": "The database operation to perform.",
        },
        "filters": {
            "type": "object",
            "description": "Filter conditions, sort, and pagination.",
            "properties": {
                "conditions": {
                    "type": "array",
                    "description": "Array of filter conditions. Each has field, op, and value.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {
                                "type": "string",
                                "description": "The field name to filter on.",
                            },
                            "op": {
                                "type": "string",
                                "enum": VALID_OPERATORS,
                                "description": "The comparison operator.",
                            },
                            "value": {
                                "description": "The value to compare against.",
                            },
                        },
                        "required": ["field", "op", "value"],
                        "additionalProperties": False,
                    },
                },
                "sort": {
                    "type": "string",
                    "description": "Field name to sort by.",
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "description": "Sort direction. Default: asc.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of results to skip.",
                },
            },
            "additionalProperties": False,
        },
    },
    "required": ["action"],
    "additionalProperties": False,
}
