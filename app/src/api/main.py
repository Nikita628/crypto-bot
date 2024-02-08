from flask import Flask, jsonify
from database.models import HistoryData, Asset
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.environ.get('UI_URL')}})

@app.route('/')
def landing_page():
    return "landing page"

@app.route('/create-history-data')
def create_history_data():
    """ HistoryData.create() """
    return 'created'

@app.route('/create-asset')
def create_asset():
    Asset.create(
        coin='USDT',
        amount=1000000,
        user_id=1
    )
    return 'created'
    

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
