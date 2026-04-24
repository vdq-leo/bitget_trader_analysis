import requests
import time
import hmac
import hashlib
import base64
import os
import json
from dotenv import load_dotenv

# Load API keys from the provided env file
ENV_PATH = '/Users/leoinv/Documents/CODE/bg_key.env'
load_dotenv(ENV_PATH)

class BitgetAPIClient:
    def __init__(self):
        self.base_url = "https://api.bitget.com"
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        self.passphrase = os.getenv("PASSPHRASE")
        
        if not self.api_key:
            print(f"CRITICAL: API_KEY not found in {ENV_PATH}")

    def _headers(self, method, path, body=""):
        timestamp = str(int(time.time() * 1000))
        message = timestamp + method + path + body
        signature = base64.b64encode(
            hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256).digest()
        ).decode()
        
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }

    def get_traders_page(self, page_no=1, page_size=100):
        """Fetch a page of elite traders."""
        path = f"/api/v2/copy/mix-broker/query-traders?pageNo={page_no}&pageSize={page_size}"
        url = self.base_url + path
        try:
            res = requests.get(url, headers=self._headers("GET", path))
            data = res.json()
            if data.get("code") != "00000":
                print(f"API Error ({path}): {data.get('code')} - {data.get('msg')}")
                return []
            return data.get("data") or []
        except Exception as e:
            print(f"Request Exception: {e}")
            return []

    def get_all_traders(self, limit=100):
        """Fetch top traders up to the limit."""
        traders = []
        PAGE_SIZE = 20
        page = 1
        while len(traders) < limit:
            batch = self.get_traders_page(page, PAGE_SIZE)
            if not batch:
                break
            traders.extend(batch)
            if len(batch) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.2)
        return traders[:limit]

    def get_trader_trades(self, trader_id, limit=20):
        """
        Fetch closed copy trades for a trader.
        We try multiple possible V2 endpoints for discovery.
        """
        endpoints = [
            f"/api/v2/copy/mix-broker/query-history-traces?traderId={trader_id}&pageSize={limit}",
            f"/api/v2/copy/mix-trader/query-trader-history-traces?traderId={trader_id}&pageSize={limit}",
            f"/api/v2/copy/mix-trader/history-traces?traderId={trader_id}&pageSize={limit}"
        ]
        
        for path in endpoints:
            try:
                url = self.base_url + path
                res = requests.get(url, headers=self._headers("GET", path))
                rj = res.json()
                if rj.get("code") == "00000" and rj.get("data"):
                    return rj["data"]
            except:
                continue
        return []
