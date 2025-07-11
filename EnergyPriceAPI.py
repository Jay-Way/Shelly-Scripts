import requests
import base64
import os
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

from dotenv import load_dotenv
load_dotenv()

CLIENT_SECRET = os.getenv('CLIENT_SECRET')
CLIENT_USER = os.getenv('CLIENT_USER')
ZIPCODE = os.getenv('ZIPCODE')

# ---------------------------
# OSTROM API MODULE
# ---------------------------

def get_ostrom_access_token() -> str:
    sample_string = CLIENT_USER + ':' + CLIENT_SECRET
    sample_string_bytes = sample_string.encode("ascii")

    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    url = "https://auth.production.ostrom-api.io/oauth2/token"
    payload = { "grant_type": "client_credentials" }
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded",
        "authorization": f"Basic {base64_string}"
    }

    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
    return response.json().get("access_token")


def fetch_ostrom_prices(token: str, zip_code: str = ZIPCODE, resolution: str = "HOUR") -> list[dict]:
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)

    start_of_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    end_of_day = datetime.combine(tomorrow.date(), time.min, tzinfo=timezone.utc)

    iso_format = "%Y-%m-%dT%H:%M:%S.000Z"
    start_date_str = start_of_day.strftime(iso_format)
    end_date_str = end_of_day.strftime(iso_format)

    params = {
        "startDate": start_date_str,
        "endDate": end_date_str,
        "resolution": resolution,
        "zip": zip_code
    }

    base_url = "https://production.ostrom-api.io/spot-prices"
    url = f"{base_url}?{urlencode(params)}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("data", [])


def get_current_gross_kwh_price(price_data: list[dict], tz=ZoneInfo("Europe/Berlin")) -> float:
    now = datetime.now(tz)
    print('Its currently ' + str(now.hour) + ':' + str(now.minute))
    for slot in price_data:
        slot_dt = datetime.fromisoformat(slot["date"].replace("Z", "+00:00"))
        if slot_dt.hour == now.hour:
            return slot["grossKwhPrice"] + slot["grossKwhTaxAndLevies"]
    raise ValueError("No matching hour slot found.")