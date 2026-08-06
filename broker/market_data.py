from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from broker.kite_client import KiteClient
from config.logging_config import get_logger

logger = get_logger("system")


class MarketDataLoader:
    """
    Fetches quote data, OHLC historical candles, and handles dataframe conversions.
    """

    def __init__(self, kite_client: KiteClient):
        self.kite_client = kite_client

    def fetch_historical_df(
        self,
        instrument_token: int,
        interval: str = "5minute",
        days_back: int = 5
    ) -> pd.DataFrame:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        from_str = from_date.strftime("%Y-%m-%d %H:%M:%S")
        to_str = to_date.strftime("%Y-%m-%d %H:%M:%S")

        try:
            records = self.kite_client.get_historical_data(
                instrument_token=instrument_token,
                from_date=from_str,
                to_date=to_str,
                interval=interval
            )

            if not records:
                return pd.DataFrame()

            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df

        except Exception as e:
            logger.error(f"Error loading historical candles for token {instrument_token}: {str(e)}")
            return pd.DataFrame()
