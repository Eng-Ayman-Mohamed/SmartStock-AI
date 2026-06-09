from enum import Enum
from typing import Optional
from datetime import date




class NLQueryAction(str, Enum):
    GET_INVENTORY    = "get_inventory"      # Current stock level for a product / SKU
    GET_SALES_REPORT = "get_sales_report"   # Historical sales within a date range
    GET_LOW_STOCK    = "get_low_stock"      # Products below a stock threshold
    FORECAST_DEMAND  = "forecast_demand"    # Prophet-based 30-day demand forecast
    GET_SUPPLIER_INFO = "get_supplier_info" # Supplier contact / lead-time data




class NLQueryFilters:
    """
    Validated container for filter values extracted from the user's NL query.
    Constructed by NLQueryOutputParser after the LLM returns JSON.
    """

    def __init__(
        self,
        product_name:  Optional[str]  = None,
        sku_code:      Optional[str]  = None,
        date_from:     Optional[str]  = None,   # ISO-8601 string  "YYYY-MM-DD"
        date_to:       Optional[str]  = None,   # ISO-8601 string  "YYYY-MM-DD"
        stock_below:   Optional[float] = None,  # numeric threshold
        supplier_name: Optional[str]  = None,
    ):
        self.product_name  = product_name
        self.sku_code      = sku_code
        self.date_from     = date_from
        self.date_to       = date_to
        self.stock_below   = stock_below
        self.supplier_name = supplier_name

    def to_dict(self) -> dict:
        """Return only the fields that were actually set (non-None)."""
        return {k: v for k, v in self.__dict__.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "NLQueryFilters":
        """Build from the raw 'filters' sub-object the LLM returns."""
        return cls(
            product_name  = data.get("product_name"),
            sku_code      = data.get("sku_code"),
            date_from     = data.get("date_from"),
            date_to       = data.get("date_to"),
            stock_below   = data.get("stock_below"),
            supplier_name = data.get("supplier_name"),
        )




class NLQueryResult:
    def __init__(self, action: NLQueryAction, filters: NLQueryFilters):
        self.action  = action
        self.filters = filters

    def to_dict(self) -> dict:
        return {
            "action":  self.action.value,
            "filters": self.filters.to_dict(),
        }



NL_QUERY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [a.value for a in NLQueryAction],
            "description": (
                "The category of database operation to perform. "
                "Must be exactly one of the five allowed values."
            ),
        },
        "filters": {
            "type": "object",
            "description": "Optional constraints extracted from the user's query.",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Full or partial product display name.",
                },
                "sku_code": {
                    "type": "string",
                    "description": "Exact SKU code, e.g. 'ABC-001'.",
                },
                "date_from": {
                    "type": "string",
                    "format": "date",
                    "description": "Start of date range, ISO-8601 (YYYY-MM-DD).",
                },
                "date_to": {
                    "type": "string",
                    "format": "date",
                    "description": "End of date range, ISO-8601 (YYYY-MM-DD).",
                },
                "stock_below": {
                    "type": "number",
                    "description": "Return only products whose available quantity is below this value.",
                },
                "supplier_name": {
                    "type": "string",
                    "description": "Supplier company name, full or partial.",
                },
            },
            "additionalProperties": False,
        },
    },
    "required": ["action"],
    "additionalProperties": False,
}