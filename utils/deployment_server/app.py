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
_CRYPTO_BOT_SIGNALS_CHAT_ID = os.getenv('CRYPTO_BOT_SIGNALS_CHAT_ID')
_CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
_CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
SEND_URL = f'https://api.telegram.org/bot{_CRYPTO_BOT_TOKEN}/sendMessage'

@app.route('/', methods=['POST'])
def do_post():
    git_event = json.loads(request.data)
    if git_event.get('ref') == 'refs/heads/migrations_and_python_server':
        result_message = 'success'

        try:
            result = call('/var/bot-app/crypto-bot/utils/scripts/git_pull', shell=True)
            if result != 0:
                result_message = 'git pull error'
            else:
                result = call('/var/bot-app/crypto-bot/utils/scripts/docker_compose_and_migrations', shell=True)
                if result != 0:
                    result_message = 'compose or migrations error'

        except:
            result_message = 'error'

        error_label = ''
        if result_message != 'success':
            error_label = '<b>ERROR</b> '

        message = f'''
<b>{error_label}Crypto-bot message</b>
<b>Action:</b> auto deployment
<b>Result:</b> {result_message}
<b>DateTime:</b> {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}'''
        response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_SIGNALS_CHAT_ID, 'parse_mode': 'html', 'text': message})

        # retry if failed
        if not response:
            count = 1
            while (not response and count <= 5):
                time.sleep(5)
                response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_SIGNALS_CHAT_ID, 'parse_mode': 'html', 'text': message})
                count += 1

        return 'prod branch action'
    else:
        return 'other branch action'


if __name__ == '__main__':
    app.run(debug=True)