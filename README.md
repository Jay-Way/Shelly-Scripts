# Python + Shelly home automation scripts

This is a collection of simple scripts using dynamic energy prices (By Ostrom) to control an LED and water boiler, and to send price data to the Shelly tariff prices endpoint.

`update_shelly_tariff_price.py`: Sends the current energy price to the tokenized Shelly URL, to display the correct energy costs in the dashboard

`dimmer_script.py`: Controls an LED brightness between 50% and 100%, based on the current energy prices

- Supports three quantiles to set the brightness, e.g., lowest third of total prices → 100% brightess, highest third → 50%, in between: 75%

`boiler_script.py`: Controls a water boiler, switching it on for an hour during the time window of lowest energy prices

`EnergyPriceAPI.py`: Reusable function to call the energy price API

# Necessary ENV vars

### Ostrom vars
CLIENT_USER=string

CLIENT_SECRET=string

ZIPCODE=int

### Shelly vars
SHELLY_TOKENIZED_URL_SECRET=base64_token