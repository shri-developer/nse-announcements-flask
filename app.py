from flask import Flask, jsonify
import requests
import json
import pytz
from datetime import datetime
import time

app = Flask(__name__)

# Set Indian Time Zone
IST = pytz.timezone('Asia/Kolkata')

# NSE API URL for corporate announcements
NSE_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities"
NSE_MAIN_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"

# Headers to mimic a real browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
}

# Store previously fetched announcements
previous_announcements = set()

def get_data(sess, cookies, url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = sess.get(url, headers=HEADERS, timeout=15, cookies=cookies)
            if response.status_code == 401:
                cookies = set_cookie(sess)
                response = sess.get(url, headers=HEADERS, timeout=15, cookies=cookies)
            return response.text if response.status_code == 200 else ""
        except requests.exceptions.ReadTimeout:
            print(f"Attempt {attempt+1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
    return ""

def set_cookie(sess):
    response = sess.get(NSE_MAIN_PAGE, headers=HEADERS, timeout=60)
    return dict(response.cookies)

def get_nse_data(sess, cookies):
    response_text = get_data(sess, cookies, NSE_URL)
    if response_text:
        try:
            json_data = json.loads(response_text)
            return json_data if isinstance(json_data, list) else []
        except json.JSONDecodeError:
            return []
    return []

def process_data():
    global previous_announcements
    with requests.Session() as sess:
        cookies = set_cookie(sess)
        data = get_nse_data(sess, cookies)
        if not data:
            return []
        new_entries = []
        current_announcements = set()
        for item in data:
            announcement_id = item.get("seq_id")
            if announcement_id:
                current_announcements.add(announcement_id)
                if announcement_id not in previous_announcements:
                    new_entries.append(item)
        previous_announcements = current_announcements
        return data if not previous_announcements else new_entries

@app.route('/get_announcements', methods=['GET'])
def get_announcements():
    announcements = process_data()
    return jsonify({
        "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        "announcements": announcements
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
