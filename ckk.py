import time
import requests
import json
from flask import Flask, request

app = Flask(__name__)

@app.route('/api', methods=['GET'])
def api():
    start_time = time.time()

    cards = request.args.get("lista", "")
    mode = request.args.get("mode", "cvv")
    amount = int(request.args.get("amount", 1))
    currency = request.args.get("currency", "usd")

    if not cards:
        return "Please enter card details"

    card_list = cards.split(",")
    results = []

    pk = 'pk_live_51HfBwmD4mk8ECiEaK52fL9vngrRWrLNtA0N2LEC9OGWMd15vtAyz2fFeKMXXWT61L5JlAZs5tePyOefl6YrXvXtc00WGdR32ky'
    sk = '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'

    for card in card_list:
        split = card.split("|")
        cc = split[0] if len(split) > 0 else ''
        mes = split[1] if len(split) > 1 else ''
        ano = split[2] if len(split) > 2 else ''
        cvv = split[3] if len(split) > 3 else ''

        if not cc or not mes or not ano or not cvv:
            results.append(f"Invalid card details for {card}")
            continue

        token_data = {
            'card[number]': cc,
            'card[exp_month]': mes,
            'card[exp_year]': ano,
            'card[cvc]': cvv
        }

        # Token creation
        response = requests.post(
            'https://api.stripe.com/v1/tokens',
            data=token_data,
            headers={
                'Authorization': f'Bearer {pk}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        token_response = response.json()
        print(f"Token response for {card}: {token_response}")  # Debugging line

        if response.status_code != 200:
            error_message = token_response.get('error', {}).get('message', 'Unknown error')
            results.append(f"Error: {error_message} for {card}")
            continue

        token_id = token_response.get('id', '')

        if not token_id:
            results.append(f"Token creation failed for {card}")
            continue

        charge_data = {
            'amount': amount * 100,
            'currency': currency,
            'source': token_id,
            'description': 'Charge for product/service'
        }

        # Charge creation
        response = requests.post(
            'https://api.stripe.com/v1/charges',
            data=charge_data,
            headers={
                'Authorization': f'Bearer {sk}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        charge_response = response.json()
        print(f"Charge response for {card}: {charge_response}")  # Debugging line

        chares = charge_response
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)

        if response.status_code == 200 and chares.get('status') == "succeeded":
            status = "CHARGED"
            resp = "Charged successfully ✅"
        else:
            error_message = chares.get('error', {}).get('message', 'Unknown error')
            decline_code = chares.get('error', {}).get('decline_code', 'No decline code')

            if decline_code == "incorrect_cvc":
                status = "LIVE"
                resp = "CCN LIVE✅ - Incorrect CVV"
            elif decline_code == "insufficient_funds":
                status = "LIVE"
                resp = "Insufficient funds✅"
            elif decline_code == "expired_card":
                status = "Declined ❌️"
                resp = "Card expired"
            elif decline_code == "stolen_card":
                status = "Declined ❌️"
                resp = "Stolen card"
            elif decline_code == "lost_card":
                status = "Declined ❌️"
                resp = "Lost card"
            else:
                status = "Declined ❌️"
                resp = f"{decline_code}: {error_message}"

        results.append(f"{status}-->{card}-->[{resp}]")

    return "<br>".join(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
