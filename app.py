import os
from bs4 import BeautifulSoup
import cloudscraper
from flask import Flask, jsonify
import requests

app = Flask(__name__)

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

TARGET_PRODUCTS = [
    {
        "name": "【丸久小山園 又玄】補貨通知！",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【丸久小山園 五十鈴】補貨通知！",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1191040c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【丸久小山園 青嵐】補貨通知！",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/11a1040c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【BTS 返鄉專車】釋票通知！",
        "url": "https://tixcraft.com/ticket/area/26_btskhbus/22784",
        "out_keywords": ["B16 高雄市 往 台南市 已售完"],
    },
]

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"}


def send_line_message(message):
    if LINE_ACCESS_TOKEN and LINE_USER_ID:
        requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={"Authorization": f"Bearer {LINE_ACCESS_TOKEN}"},
            json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]},
        )


@app.route("/")
@app.route("/check")
def check_stock():
    scraper = cloudscraper.create_scraper()
    results, in_stock = [], []

    for item in TARGET_PRODUCTS:
        try:
            res = scraper.get(item["url"], headers=HEADERS, timeout=15)
            if res.status_code != 200:
                results.append(
                    {"name": item["name"], "status": "HTTP_ERROR", "code": res.status_code}
                )
                continue

            page_text = BeautifulSoup(res.text, "html.parser").get_text()
            is_out = any(kw in page_text for kw in item["out_keywords"])
            status = "OUT_OF_STOCK" if is_out else "IN_STOCK"

            if not is_out:
                in_stock.append(f"🎉 {item['name']}\n\n{item['url']}")

            results.append({"name": item["name"], "status": status, "url": item["url"]})
        except Exception as e:
            results.append({"name": item["name"], "status": "ERROR", "error": str(e)})

    if in_stock:
        send_line_message("⚠️\n\n" + "\n\n".join(in_stock))

    return jsonify({"checked_count": len(TARGET_PRODUCTS), "details": results}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
