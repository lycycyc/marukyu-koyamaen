from flask import Flask, jsonify
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

URL = "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1"
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

def send_line_message(message):
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        return "未設定 Token"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
    return response.status_code

@app.route("/")
@app.route("/check")
def check_stock():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text().lower()

        out_of_stock_keywords = ["out of stock", "sold out", "temporarily unavailable"]
        is_out_of_stock = any(kw in page_text for kw in out_of_stock_keywords)
        add_to_cart_btn = soup.select_one(".single_add_to_cart_button")

        if add_to_cart_btn and not is_out_of_stock:
            message = f"🎉 丸久小山園商品確定補貨了！\n請盡快前往搶購：\n{URL}"
            send_line_message(message)
            return jsonify({"status": "IN_STOCK", "message": "已發送通知"}), 200
        else:
            return jsonify({"status": "OUT_OF_STOCK", "message": "目前缺貨中"}), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
