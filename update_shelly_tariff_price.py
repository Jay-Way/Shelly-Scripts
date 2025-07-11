import requests
from datetime import datetime, time, timezone, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from EnergyPriceAPI import fetch_ostrom_prices, get_current_gross_kwh_price, get_ostrom_access_token

from dotenv import load_dotenv
load_dotenv()

SHELLY_TOKENIZED_URL_SECRET = os.getenv('SHELLY_TOKENIZED_URL_SECRET')

# ---------------------------
# SHELLY COMMUNICATION
# ---------------------------

def update_shelly_tariff(url: str, price_eur_per_kwh: float) -> requests.Response:
    headers = {
        "Content-Type": "application/json"
    }
    payload = { "price": price_eur_per_kwh }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response

def main():
    print("------ Shelly tariff price script ------")

    # API credentials
    shelly_url = "https://shelly-187-eu.shelly.cloud/v2/user/pp-ltu/" + SHELLY_TOKENIZED_URL_SECRET

    try:
        token = get_ostrom_access_token()
        price_data = fetch_ostrom_prices(token)
        current_brutto = get_current_gross_kwh_price(price_data) / 100
        response = update_shelly_tariff(shelly_url, current_brutto)
        print(f"Sent energy price to Shelly: {response.text}")
    except Exception as e:
        print(f"Error occurred: {e}")

    print("------ ------ ------")


if __name__ == "__main__":
    main()
