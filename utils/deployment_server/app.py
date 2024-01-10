from flask import Flask, request
import os
from dotenv import load_dotenv
from subprocess import call
from datetime import datetime
import time
import requests
import json

app = Flask(__name__)


load_dotenv()
_CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
_CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
SEND_URL = f'https://api.telegram.org/bot{_CRYPTO_BOT_TOKEN}/sendMessage'


@app.route('/', methods=['POST'])
def do_post():
    git_event = json.loads(request.data)
    if git_event.get('ref') == 'refs/heads/prod':
        update_result = 'success'

        try:
            call('/var/bot-app/crypto-bot/utils/scripts/deployment 2> /var/bot-app/logs/deployment_err.log', shell=True)
        except:
            update_result = 'error'

        message = f'''
<b>Crypto-bot message</b>
<b>Action:</b> update files
<b>Result:</b> {update_result}
<b>DateTime:</b> {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}'''
        response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_STATUS_CHAT_ID, 'parse_mode': 'html', 'text': message})

        # retry if failed
        if not response:
            count = 1
            while (not response and count <= 5):
                time.sleep(5)
                response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_STATUS_CHAT_ID, 'parse_mode': 'html', 'text': message})
                count += 1

        return 'prod branch action'
    else:
        return 'other branch action'


if __name__ == '__main__':
    app.run(debug=True)