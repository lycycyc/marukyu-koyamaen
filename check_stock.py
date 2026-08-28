import os
import requests
from bs4 import BeautifulSoup

# 設定要追蹤的網址
URL = "https://www.marukyu-koyamaen.co.jp/english/shop/products/1171020c1"
LINE_TOKEN = os.environ.get("LINE_TOKEN")


def send_line_notify(message):
  """發送 LINE 通知"""
  if not LINE_TOKEN:
    print("未設定 LINE_TOKEN")
    return

  headers = {"Authorization": f"Bearer {LINE_TOKEN}"}
  data = {"message": message}
  response = requests.post(
      "https://notify-api.line.me/api/notify", headers=headers, data=data
  )

  if response.status_code == 200:
    print("LINE 通知發送成功！")
  else:
    print(f"LINE 通知發送失敗，錯誤碼：{response.status_code}")


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

    # ---------------------------------------------------------
    # 提示：以下文字與標籤需根據該網站實際顯示「售完/缺貨」的字眼調整
    # 假設網站缺貨時會出現 "Out of stock" 或 "Sold out"
    # ---------------------------------------------------------
    page_text = soup.get_text()

    # 這裡以檢查網頁是否包含 "Out of stock" 為例
    # 如果網站有明顯的按鈕或文字，建議針對特定 HTML 標籤抓取會更準確
    if "Out of stock" in page_text or "Sold out" in page_text:
      print("目前仍然缺貨中...")
    else:
      # 如果找不到缺貨字眼，可能代表有貨了！
      message = (
          f"\n🎉 丸久小山園商品可能補貨了！\n請盡快前往搶購：\n{URL}"
      )
      send_line_notify(message)

  except Exception as e:
    print(f"發生錯誤：{e}")


if __name__ == "__main__":
  check_product_stock()
