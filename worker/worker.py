import requests
import time
from os import environ

DOMAIN_NAME = environ.get('DOMAIN_NAME')
MAILGUN_URL = f"https://api.mailgun.net/v3/{DOMAIN_NAME}/messages"
MAILGUN_KEY = environ.get('API_KEY')
MAILGUN_EMAIL = f"mailgun@{DOMAIN_NAME}"

# send message to email
def send_message(message, email, delayTime):
    time.sleep(delayTime)
    if not email:
        return
    else:
        return requests.post(
		MAILGUN_URL,
		auth=("api", MAILGUN_KEY),
		data={"from": f"Excited User <{MAILGUN_EMAIL}>",
			"to": email,
			"subject": "Fire In Your Area",
			"text": message})