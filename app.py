from flask import Flask, jsonify
import requests
import json
import pytz
from datetime import datetime

# Set Indian Time Zone
IST = pytz.timezone('Asia/Kolkata')

# NSE API URL for corporate announcements
NSE_URL = "https://www.nseindia.com/api/corporate-announcements?index=equities"
NSE_MAIN_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"

# Headers to mimic a real browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
}

app = Flask(__name__)


def get_data(sess, cookies, url, retries=3, delay=5):
    """Fetch data from NSE API with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0 Safari/537.36',
        'Referer': 'https://www.nseindia.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    for attempt in range(retries):
        try:
            response = sess.get(url, headers=headers, timeout=20, cookies=cookies)
            if response.status_code == 403:
                print(f"[ERROR] NSE blocking request (403 Forbidden). Retrying in {delay} seconds...")
                time.sleep(delay)
                continue  # Try again
            
            if response.status_code == 200:
                return response.text
            
        except requests.exceptions.ReadTimeout:
            print(f"[ERROR] Request timed out. Retrying in {delay} seconds...")
            time.sleep(delay)

    return ""  # Return empty response after max retries


def set_cookie(sess):
    """Set cookies by making a request to the NSE main page"""
    response = sess.get(NSE_MAIN_PAGE, headers=HEADERS, timeout=60)
    return dict(response.cookies)


def get_nse_data():
    """Fetch and parse NSE announcements JSON data"""
    with requests.Session() as sess:
        cookies = set_cookie(sess)
        response_text = get_data(sess, cookies, NSE_URL)
        if response_text:
            try:
                json_data = json.loads(response_text)
                return json_data if isinstance(json_data, list) else []
            except json.JSONDecodeError:
                return []
        return []


def get_current_time():
    """Returns the current timestamp in IST"""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


@app.route('/get_announcements', methods=['GET'])
def get_announcements():
    """API Endpoint to get NSE announcements"""
    data = get_nse_data()
    if not data:
        return jsonify({"status": "error", "message": "No data received from NSE API"}), 500

    formatted_data = []
    for item in data:
        formatted_data.append({
            "company": item.get("symbol", "N/A"),
            "title": item.get("desc", "N/A"),
            "short_description": item.get("attchmntText", "N/A"),
            "timestamp": item.get("sort_date", "N/A"),
            "link": item.get("attchmntFile", "#")
        })
    
    return jsonify({"status": "success", "timestamp": get_current_time(), "announcements": formatted_data})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
