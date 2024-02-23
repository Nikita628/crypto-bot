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
_CLEAR_DATA_TOKEN = os.getenv('CLEAR_DATA_TOKEN')
_CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
_CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
SEND_URL = f'https://api.telegram.org/bot{_CRYPTO_BOT_TOKEN}/sendMessage'

@app.route('/', methods=['POST', 'GET'])
def do_action():
    if request.method == 'POST':
        git_event = json.loads(request.data)
        if git_event.get('ref') == 'refs/heads/prod':
            result_message = 'success'

            try:
                call('chmod +x /var/bot-app/crypto-bot/utils/scripts/git_pull', shell=True)
                result = call('/var/bot-app/crypto-bot/utils/scripts/git_pull', shell=True)
                if result != 0:
                    result_message = 'git pull error'
                else:
                    call('chmod +x /var/bot-app/crypto-bot/utils/scripts/docker_compose_and_migrations', shell=True)
                    result = call('/var/bot-app/crypto-bot/utils/scripts/docker_compose_and_migrations', shell=True)
                    if result != 0:
                        result_message = 'compose or migrations error'

            except Exception as e:
                if not e:
                    e = 'unknown'
                result_message = e

            error_label = ''
            if result_message != 'success':
                error_label = '<b>ERROR</b> '

            message = f'''
<b>{error_label}Crypto-bot message</b>
<b>Action:</b> auto deployment
<b>Result:</b> {result_message}
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
    else:
        action = request.args.get('action')
        clear_data_token = request.args.get('token')
        strategy = request.args.get('strategy')
        result_message = 'success'
        if action == 'clear_data' and clear_data_token == _CLEAR_DATA_TOKEN:
            if not strategy:
                strategy = ''

            call('chmod +x /var/bot-app/crypto-bot/utils/scripts/clear_data', shell=True)
            result = call('strategy="' + strategy + '" /var/bot-app/crypto-bot/utils/scripts/clear_data', shell=True)

            if result != 0:
                result_message = 'error on delete or start docker'
        else:
            result_message = 'invalid credentials'

        if not strategy:
            strategy = 'all'
        error_label = ''
        if result_message != 'success':
            error_label = '<b>ERROR</b> '
        message = f'''
<b>{error_label}Crypto-bot message</b>
<b>Action:</b> clear data
<b>strategy:</b> {strategy}
<b>Result:</b> {result_message}
<b>DateTime:</b> {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}'''
        response = requests.post(SEND_URL, json={'chat_id': _CRYPTO_BOT_STATUS_CHAT_ID, 'parse_mode': 'html', 'text': message})
        return result_message

if __name__ == '__main__':
    app.run(debug=True)