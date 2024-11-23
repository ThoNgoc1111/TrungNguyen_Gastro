# paypal.py
import requests
from django.conf import settings

def get_access_token():
    url = f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
    }
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data, auth=auth)
    response.raise_for_status()
    return response.json().get("access_token")


def create_order(amount, currency="USD"):
    url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders"
    token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": currency, "value": amount}}
        ],
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def capture_order(order_id):
    url = f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{order_id}/capture"
    token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    response = requests.post(url, headers=headers)
    response.raise_for_status()
    return response.json()
