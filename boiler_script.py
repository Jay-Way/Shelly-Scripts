import requests
from datetime import datetime, time, timezone, timedelta
import time as t
from urllib.parse import urlencode
from typing import Optional, Dict, Any
from zoneinfo import ZoneInfo
import requests
from urllib.parse import urljoin
from EnergyPriceAPI import fetch_ostrom_prices, get_current_gross_kwh_price, get_ostrom_access_token

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
    # Find the item with the lowest netKwhPrice
    lowest = min(data, key=lambda x: x.get("netKwhPrice", float("inf")))

    return {
        "date": lowest["date"],
        "netKwhPrice": lowest["netKwhPrice"],
        "grossKwhPrice": lowest["grossKwhPrice"],
        "grossKwhTaxAndLevies": lowest["grossKwhTaxAndLevies"]
    }

def main():
    print("------ Shelly boiler relais script ------")
    try:
        token = get_ostrom_access_token()
        price_data = fetch_ostrom_prices(token)
        result = find_lowest_net_kwh_price(price_data)
        cheapestDateTime = result['date']
        now = datetime.now(tz=ZoneInfo("Europe/Berlin"))
        utc_dt = datetime.strptime(cheapestDateTime, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
        cheapestDateTimeLocalTime = utc_dt.astimezone(ZoneInfo("Europe/Berlin"))
        grossKwhPrice = result['grossKwhPrice']
        grossKwhTaxAndLevies = result['grossKwhTaxAndLevies']
        print('Price is lowest at this time: ' + cheapestDateTimeLocalTime.strftime('%H:%I') + ' with ' + str(grossKwhPrice + grossKwhTaxAndLevies) + ' cents.')
        diff = cheapestDateTimeLocalTime - now

        # Extract hours and minutes manually
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if total_seconds < 0:
            print('Boiler was already on today, waiting until tomorrow...')
        else:
            formatted = f"{hours}:{minutes:02d}"
            print('Boiler will switch on in ' + formatted + ' hours.')
            if is_same_hour(cheapestDateTimeLocalTime):
                print('Energy price is low, switching boiler on...')
                switch_shelly_http('on')
                t.sleep(3600)
                print('Switching boiler off')
                switch_shelly_http('off')
            else:
                print('Currently not in a window with cheap energy prices, waiting...')
    except Exception as e:
        print(f"Error occurred: {e}")
    print("------ ------ ------")

if __name__ == "__main__":
    main()