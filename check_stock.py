import os
from bs4 import BeautifulSoup
import requests

# 設定要追蹤的丸久小山園商品網址
URL = "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1"
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")


def send_line_message(message):
  """使用 LINE Messaging API 發送推播通知"""
  if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
    print("未設定 LINE_ACCESS_TOKEN 或 LINE_USER_ID")
    return

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

  if response.status_code == 200:
    print("LINE 訊息發送成功！")
  else:
    print(
        "LINE 訊息發送失敗，錯誤碼："
        f" {response.status_code}, 內容：{response.text}"
    )


def check_product_stock():
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  try:
    response = requests.get(URL, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 1. 取得網頁所有文字並轉為小寫，徹底解決大小寫差異問題
    page_text = soup.get_text().lower()

    # 2. 定義常見的缺貨關鍵字（全部小寫）
    out_of_stock_keywords = [
        "out of stock",
        "sold out",
        "temporarily unavailable",
    ]
    is_out_of_stock = any(kw in page_text for kw in out_of_stock_keywords)

    # 3. 檢查是否有 WooCommerce 的「加入購物車」按鈕
    add_to_cart_btn = soup.select_one(".single_add_to_cart_button")

    # 4. 判斷邏輯：必須「有加入購物車按鈕」且「完全沒有出現缺貨字眼」
    if add_to_cart_btn and not is_out_of_stock:
      message = f"🎉 丸久小山園商品確定補貨了！\n請盡快前往搶購：\n{URL}"
      print("偵測到商品有貨，準備發送 LINE 通知...")
      send_line_message(message)
    else:
      print("目前商品仍處於缺貨狀態。")

  except Exception as e:
    print(f"發生錯誤：{e}")


if __name__ == "__main__":
  check_product_stock()
