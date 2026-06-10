import logging

import pandas as pd

logger = logging.getLogger(__name__)

MIN_DATA_POINTS = 30
OUTLIER_SIGMA = 3.0


def _get_repo():
    """Lazy import to avoid Django AppRegistryNotReady on pure-function imports."""
    from .repositories import ForecastingRepository

    return ForecastingRepository()


def fetch_sales_data(sku_id: int) -> pd.DataFrame:
    """
    Data access wrapper - only function with Django ORM dependency.
    Returns raw DataFrame with 'ds' (date) and 'y' (quantity_sold) columns.
    """
    repo = _get_repo()
    sales_qs = repo.get_sales_for_sku(sku_id)

    df = pd.DataFrame([{'ds': r.date, 'y': float(r.quantity_sold)} for r in sales_qs])

    if not df.empty:
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.sort_values('ds').reset_index(drop=True)

    return df


def fill_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reindex to continuous daily date range, filling missing dates with y=0.
    Preserves original min/max date boundaries.
    """
    if df.empty:
        return df

    df = df.copy()
    full_range = pd.date_range(start=df['ds'].min(), end=df['ds'].max(), freq='D')
    df = df.set_index('ds').reindex(full_range).fillna({'y': 0.0}).rename_axis('ds').reset_index()
    return df


def cap_outliers(df: pd.DataFrame, sigma: float = OUTLIER_SIGMA) -> pd.DataFrame:
    """
    Cap upper outliers at mean + sigma * std.
    Lower outliers (negative sales) are not capped since sales >= 0.
    """
    if df.empty or df['y'].std() == 0:
        return df

    df = df.copy()
    mean_y = df['y'].mean()
    std_y = df['y'].std()
    upper_bound = mean_y + sigma * std_y

    df['y'] = df['y'].clip(upper=upper_bound)
    return df


def validate_minimum_data(df: pd.DataFrame, min_records: int = MIN_DATA_POINTS) -> bool:
    """
    Check if DataFrame meets minimum record threshold for Prophet.
    """
    return len(df) >= min_records


def _log_insufficient_data(sku_code: str, record_count: int) -> None:
    """
    Log structured JSON warning for insufficient data.
    """
    logger.warning(
        'Insufficient forecast data for SKU',
        extra={
            'event': 'INSUFFICIENT_FORECAST_DATA',
            'sku_code': sku_code,
            'record_count': record_count,
            'threshold': MIN_DATA_POINTS,
            'action': 'fallback_to_moving_average',
        },
    )


def prepare_forecast_dataframe(sku_id: int) -> pd.DataFrame | None:
    """
    Main single-SKU ingestion pipeline.
    Returns cleaned DataFrame with 'ds' and 'y' columns, or None if insufficient data.
    """
    repo = _get_repo()
    sku = repo.get_sku(sku_id)

    df = fetch_sales_data(sku_id)

    if df.empty:
        _log_insufficient_data(sku.code, 0)
        return None

    df = fill_missing_dates(df)
    df = cap_outliers(df)

    if not validate_minimum_data(df):
        _log_insufficient_data(sku.code, len(df))
        return None

    return df[['ds', 'y']].copy()


def prepare_all_forecast_data() -> tuple[dict[str, pd.DataFrame], list[str]]:
    """
    Batch ingestion pipeline for all active SKUs.
    Returns (dataframes_by_sku_code, excluded_sku_codes).
    """
    repo = _get_repo()
    sales_by_sku = repo.get_sales_for_all_skus()

    dataframes: dict[str, pd.DataFrame] = {}
    excluded: list[str] = []

    for sku_code, sales_qs in sales_by_sku.items():
        df = pd.DataFrame([{'ds': r.date, 'y': float(r.quantity_sold)} for r in sales_qs])

        if df.empty:
            _log_insufficient_data(sku_code, 0)
            excluded.append(sku_code)
            continue

        df['ds'] = pd.to_datetime(df['ds'])
        df = df.sort_values('ds').reset_index(drop=True)

        df = fill_missing_dates(df)
        df = cap_outliers(df)

        if not validate_minimum_data(df):
            _log_insufficient_data(sku_code, len(df))
            excluded.append(sku_code)
            continue

        dataframes[sku_code] = df[['ds', 'y']].copy()

    return dataframes, excluded
