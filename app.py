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
        "referer": "https://www.marukyu-koyamaen.co.jp/",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【丸久小山園 五十鈴】補貨通知！",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1191040c1",
        "referer": "https://www.marukyu-koyamaen.co.jp/",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【丸久小山園 青嵐】補貨通知！",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/11a1040c1",
        "referer": "https://www.marukyu-koyamaen.co.jp/",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "name": "【BTS 返鄉專車】釋票通知！",
        "url": "https://tixcraft.com/ticket/area/26_btskhbus/22784",
        "referer": "https://tixcraft.com/",
        "out_keywords": ["B16 高雄市 往 台南市 已售完"],
    },
]

def send_line_message(message):
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("未設定 LINE Token 或 User ID")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }
    response = requests.post(
        "https://api.line.me/v2/bot/message/push", headers=headers, json=data
    )
    return response.status_code

@app.route("/")
@app.route("/check")
def check_stock():
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    results = []
    in_stock_products = []

    for item in TARGET_PRODUCTS:
        product_name = item["name"]
        url = item["url"]
        out_keywords = item["out_keywords"]
        referer = item.get("referer", url)

        custom_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": referer,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            response = scraper.get(url, headers=custom_headers, timeout=15)

            if response.status_code != 200:
                results.append({
                    "name": product_name,
                    "status": "HTTP_ERROR",
                    "code": response.status_code,
                })
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            page_text = soup.get_text()

            is_out_of_stock = any(kw in page_text for kw in out_keywords)

            if not is_out_of_stock:
                status = "IN_STOCK"
                in_stock_products.append(f"🎉 {product_name}\n\n{url}")
            else:
                status = "OUT_OF_STOCK"

            results.append(
                {"name": product_name, "status": status, "url": url}
            )

        except Exception as e:
            results.append(
                {"name": product_name, "status": "ERROR", "error": str(e)}
            )

    if in_stock_products:
        combined_message = "⚠️\n\n" + "\n\n".join(in_stock_products)
        send_line_message(combined_message)

    return jsonify({"checked_count": len(TARGET_PRODUCTS), "details": results}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
