from flask import Flask, request
import os
from dotenv import load_dotenv
from subprocess import call
from datetime import datetime
import requests
import json

app = Flask(__name__)

load_dotenv()
CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')


@app.route('/', methods=['GET', 'POST'])
def do_post():
    if request.method == 'POST':
        post_data = json.loads(request.data)
        if post_data.get('ref') == 'refs/heads/migrations_and_python_server':
            try:
                call("/var/www/scripts/deploying 2> /var/www/logs/deploying_err.log", shell=True)
                SEND_URL = f'https://api.telegram.org/bot{CRYPTO_BOT_TOKEN}/sendMessage'
                message = f'<b>Crypto-bot message</b>\n'
                message += f'<b>Action:</b> update files\n'
                message += f'<b>Result:</b> success\n'
                message += f'<b>DateTime:</b> ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                response = requests.post(SEND_URL, json={'chat_id': CRYPTO_BOT_STATUS_CHAT_ID, 'parse_mode': 'html', 'text': message})
            except:
                return 'Update error. Calling bash script is crashed'
            return 'prod branch action'
        else:
            return 'other branch action'

if __name__ == '__main__':
    app.run(debug=True)