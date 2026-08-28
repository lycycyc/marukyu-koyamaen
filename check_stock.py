import os
from bs4 import BeautifulSoup
import requests

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
    page_text = soup.get_text()

    if "Out of stock" in page_text or "Sold out" in page_text:
      print("目前仍然缺貨中...")
    else:
      message = (
          f"🎉 丸久小山園商品可能補貨了！\n請盡快前往搶購：\n{URL}"
      )
      send_line_message(message)

  except Exception as e:
    print(f"發生錯誤：{e}")


if __name__ == "__main__":
  check_product_stock()
