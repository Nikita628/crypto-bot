import os
from dotenv import load_dotenv
from subprocess import call
from datetime import datetime
import time
import requests
import json

load_dotenv()
_CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
_CRYPTO_BOT_SIGNALS_CHAT_ID = os.getenv('CRYPTO_BOT_SIGNALS_CHAT_ID')
_CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
SEND_URL = f'https://api.telegram.org/bot{_CRYPTO_BOT_TOKEN}/sendMessage'

update_result = 'success'

message = f'''
<b>Crypto-bot message</b>
<b>Action:</b> update files
<b>Result:</b> {update_result}
<b>DateTime:</b> {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}'''
response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_SIGNALS_CHAT_ID, 'parse_mode': 'html', 'text': message})

print(response)

# retry if failed
if not response:
    count = 1
    while (not response and count <= 5):
        time.sleep(5)
        response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_SIGNALS_CHAT_ID, 'parse_mode': 'html', 'text': message})
        count += 1