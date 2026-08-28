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

    # 檢查網頁中是否有 WooCommerce 的加入購物車按鈕 (通常有 .single_add_to_cart_button)
    # 或者直接檢查網頁文字是否包含明確的「有貨」訊號，並排除缺貨狀態
    
    # 找尋加入購物車按鈕
    add_to_cart_btn = soup.select_one(".single_add_to_cart_button")
    
    # 同時檢查網頁上常見的缺貨字眼
    page_text = soup.get_text()
    is_out_of_stock = "Out of stock" in page_text or "Sold out" in page_text

    # 判斷邏輯：必須「有加入購物車按鈕」且「沒有出現缺貨字眼」，才代表真的有貨！
    if add_to_cart_btn and not is_out_of_stock:
      message = (
          f"🎉 丸久小山園商品確定補貨了！\n請盡快前往搶購：\n{URL}"
      )
      print("偵測到商品有貨，準備發送 LINE 通知...")
      send_line_message(message)
    else:
      print("目前商品仍處於缺貨狀態（未檢測到購買按鈕或顯示缺貨）。")

  except Exception as e:
    print(f"發生錯誤：{e}")


if __name__ == "__main__":
  check_product_stock()
