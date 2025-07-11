import requests
from datetime import datetime, time, timezone, timedelta
import time as t
from urllib.parse import urlencode, urljoin
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
from EnergyPriceAPI import fetch_ostrom_prices, get_current_gross_kwh_price, get_ostrom_access_token
import numpy as np


def is_same_hour(cheapestDateTimeLocalTime) -> bool:
    target = cheapestDateTimeLocalTime
    now = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    return (
        now.hour == target.hour
    )

def switch_shelly_http(state: str, base_url: str = "http://192.168.178.32/relay/0") -> None:
    state = state.lower()
    if state not in {"on", "off"}:
        raise ValueError("state must be 'on' or 'off'")

    target = f"{base_url}?turn={state}"
    resp = requests.get(target, timeout=3)
    resp.raise_for_status()
    print(f"Relay switched {state}: {resp.status_code}")


def find_lowest_net_kwh_price(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    entries = data.get("data", [])
    if not entries:
        return None

    lowest = min(entries, key=lambda x: x.get("netKwhPrice", float("inf")))

    return {
        "date": lowest["date"],
        "netKwhPrice": lowest["netKwhPrice"],
        "grossKwhPrice": lowest["grossKwhPrice"],
        "grossKwhTaxAndLevies": lowest["grossKwhTaxAndLevies"]
    }

def get_prices(prices):
    priceMap = []
    now = datetime.now(tz=ZoneInfo("Europe/Berlin"))
    for price in prices:
        dateTime = price['date']

        utc_dt = datetime.strptime(dateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))

        dateTimeLocalTime = utc_dt.astimezone(ZoneInfo("Europe/Berlin"))

        priceKwhNet = price['netKwhPrice']
        priceMap.append(price['netKwhPrice'])
    return priceMap

def classify_prices(prices):
    q33 = np.quantile(prices, 0.33)
    q66 = np.quantile(prices, 0.66)

    brightness_schedule = []
    for price in prices:
        if price <= q33:
            brightness = 100
        elif price <= q66:
            brightness = 75
        else:
            brightness = 50
        brightness_schedule.append(brightness)
    return brightness_schedule

def set_shelly_brightness(level, lightState):
    try:
        url = f"http://192.168.178.33/light/0?turn={lightState}&brightness={level}"
        print('Calling ' + url + '...')
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        print(f"[INFO] Helligkeit auf {level}% gesetzt.")
    except requests.RequestException as e:
        print(f"[ERROR] Fehler beim Setzen der Helligkeit: {e}")


def main():
    print("------ Shelly Dimmer relais script ------")
    try:
        token = get_ostrom_access_token()
        price_data = fetch_ostrom_prices(token)
        prices = get_prices(price_data)
        now = datetime.now(tz=ZoneInfo("Europe/Berlin"))
        hour = now.hour
        quantilePrices = classify_prices(prices)
        brightness = quantilePrices[hour]

        print(f"[{now}] Preis: {prices[hour]:.3f} ?/kWh -> {brightness}%")
        print('Current hour is: ' + str(now.hour))

        if 12 <= now.hour < 24:
            lightState = 'on'
        else:
            lightState = 'off'

        print('Light should currently be ' + lightState)
        set_shelly_brightness(brightness, lightState)
    except Exception as e:
        print(f"Error occurred: {e}")
    print("------ ------ ------")


if __name__ == "__main__":
    main()