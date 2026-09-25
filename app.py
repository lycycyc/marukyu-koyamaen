import base64
import json
import os
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import requests

app = Flask(__name__)

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

TARGET_PRODUCTS = [
    {
        "id": "Yugen",
        "name": "【又玄】",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "id": "Isuzu",
        "name": "【五十鈴】",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1191040c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "id": "Aoarashi",
        "name": "【青嵐】",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/11a1040c1",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
    {
        "id": "Hojicha",
        "name": "【焙茶 A】",
        "url": "https://www.marukyu-koyamaen.co.jp/english/shop/products/1233100c7",
        "out_keywords": ["This product is currently out of stock and unavailable."],
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0"
}


def send_line_message(message):
    if LINE_ACCESS_TOKEN and LINE_USER_ID:
        requests.post(
            "https://api.line.me/v2/bot/message/push",
            headers={"Authorization": f"Bearer {LINE_ACCESS_TOKEN}"},
            json={"to": LINE_USER_ID, "messages": [{"type": "text", "text": message}]},
        )


def get_github_status():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {}, None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/status.json"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    return {}, None


def update_github_status(new_status_dict, sha):
    if not GITHUB_TOKEN or not GITHUB_REPO or not sha:
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/status.json"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    content_str = json.dumps(new_status_dict, indent=2)
    content_encoded = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    
    data = {
        "message": "Auto update stock status",
        "content": content_encoded,
        "sha": sha
    }
    requests.put(url, headers=headers, json=data)


@app.route("/")
@app.route("/check")
def check_stock():
    results, in_stock, out_stock = [], [], []
    
    old_status_dict, file_sha = get_github_status()
    new_status_dict = old_status_dict.copy() if old_status_dict else {}
    status_changed = False

    for item in TARGET_PRODUCTS:
        pid = item["id"]
        try:
            res = requests.get(item["url"], headers=HEADERS, timeout=15)
            if res.status_code != 200:
                results.append({
                    "name": item["name"],
                    "status": "HTTP_ERROR",
                    "code": res.status_code
                })
                continue

            is_out = any(kw in BeautifulSoup(res.text, "html.parser").get_text() for kw in item["out_keywords"])
            current_status = "OUT_OF_STOCK" if is_out else "IN_STOCK"
            
            last_status = old_status_dict.get(pid, "OUT_OF_STOCK")

            if last_status == "OUT_OF_STOCK" and current_status == "IN_STOCK":
                in_stock.append(f"{item['name']}\n{item['url']}")
                status_changed = True
            elif last_status == "IN_STOCK" and current_status == "OUT_OF_STOCK":
                out_stock.append(f"{item['name']}\n{item['url']}")
                status_changed = True

            new_status_dict[pid] = current_status

            results.append({
                "name": item["name"],
                "status": current_status,
                "url": item["url"]
            })
        except Exception as e:
            results.append({
                "name": item["name"],
                "status": "ERROR",
                "error": str(e)
            })

    if status_changed and file_sha:
        update_github_status(new_status_dict, file_sha)

    if in_stock:
        send_line_message("🍵 【丸久小山園】補貨通知\n\n\n\n" + "\n\n\n".join(in_stock))

    if out_stock:
        send_line_message("🍵 【丸久小山園】售完通知\n\n\n\n" + "\n\n\n".join(out_stock))

    return jsonify({
        "checked_count": len(TARGET_PRODUCTS),
        "details": results
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
