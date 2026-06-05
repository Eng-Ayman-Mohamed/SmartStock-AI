class ProphetEngine:
    """Isolated Prophet ML logic — no Django imports."""

    def predict(self, sku) -> list[dict]:
        return [
            {
                "sku": sku,
                "forecast_date": "2025-01-01",
                "predicted_quantity": 0,
                "lower_bound": 0,
                "upper_bound": 0,
            }
        ]
