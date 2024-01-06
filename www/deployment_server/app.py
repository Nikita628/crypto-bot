from flask import Flask, request
import os
from dotenv import load_dotenv
from subprocess import call
from datetime import datetime
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def do_post():
    load_dotenv()
    CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
    CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
    if request.method == 'POST':
        if request.args.get('ref') == 'refs/heads/migrations_and_python_server':
            with open('./output.txt', 'a') as f:
                f.write('Hi')
            return 'r'
        else:
            with open('./output.txt', 'a') as f:
                f.write('TTTTT')
            return CRYPTO_BOT_STATUS_CHAT_ID + CRYPTO_BOT_TOKEN
    else:
        return CRYPTO_BOT_STATUS_CHAT_ID + CRYPTO_BOT_TOKEN

if __name__ == '__main__':
    app.run(debug=True)