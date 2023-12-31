from subprocess import call
from datetime import datetime
import requests
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = "193.233.133.115"
serverPort = 8000

class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data_unicode = post_data.decode('utf-8')
        data = json.loads(data_unicode)
        if data.get('ref') == 'refs/heads/prod':
            try:
                call("./scripts/files_update", shell=True)

                TOKEN = '6874810972:AAG6QTkvcU21ift9Ddpfe3IQNEgj5DxAqOw'
                CHAT_ID = '-1002072371752'
                SEND_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
                message = f'<b>Crypto-bot message</b>\n'
                message += f'<b>Action:</b> update files\n'
                message += f'<b>Result:</b> success\n'
                message += f'<b>DateTime:</b> ' + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                response = requests.post(SEND_URL, json={'chat_id': CHAT_ID, 'parse_mode': 'html', 'text': message})
                if response:
                    print('result is sent to telegram')
                else:
                    print('error sending to telegram')

            except:
                print('update error')


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")