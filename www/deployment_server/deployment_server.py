import os
from dotenv import load_dotenv
from subprocess import call
from datetime import datetime
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "193.233.133.115"
serverPort = 8000

class DeploymentServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data_unicode = post_data.decode('utf-8')
        data = json.loads(data_unicode)
        if data.get('ref') == 'refs/heads/migrations_and_python_server':
            try:
                call("./scripts/deploying 2> /var/www/logs/deploying_err.log", shell=True)

                load_dotenv()
                CRYPTO_BOT_STATUS_CHAT_ID = os.getenv('CRYPTO_BOT_STATUS_CHAT_ID')
                CRYPTO_BOT_TOKEN = os.getenv('CRYPTO_BOT_TOKEN')
                SEND_URL = f'https://api.telegram.org/bot{CRYPTO_BOT_TOKEN}/sendMessage'
                message = f'<b>Crypto-bot message</b>\n'
                message += f'<b>Action:</b> update files\n'
                message += f'<b>Result:</b> success\n'
                message += f'<b>DateTime:</b> ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                response = requests.post(SEND_URL, json={'chat_id': CRYPTO_BOT_STATUS_CHAT_ID, 'parse_mode': 'html', 'text': message})
                if response:
                    print('result is sent to telegram')
                else:
                    print('error sending to telegram')

            except:
                print('update error')


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), DeploymentServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")