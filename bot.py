import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URL = "https://www.londonstockexchange.com/stock/UZNF/national-investment-fund-of-the-republic-of-uzbekistan-jsc/company-page"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

STATE_FILE = "state.json"


def send_message(message):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(telegram_url, data=payload)


def extract_value(text, label):
    pattern = rf"{label}\s+([\d.,]+)"
    match = re.search(pattern, text)

    if match:
        return match.group(1)

    return "N/A"


def get_market_data():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    open_price = extract_value(text, "Open")
    close_price = extract_value(text, "Previous close")
    high_price = extract_value(text, "High")
    low_price = extract_value(text, "Low")
    volume = extract_value(text, "Volume")

    trade_day_signature = (
        f"{open_price}_{close_price}_{high_price}_{low_price}_{volume}"
    )

    return {
        "signature": trade_day_signature,
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "low": low_price,
        "volume": volume
    }


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    return None


def save_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file)


def check_market_update():
    current_data = get_market_data()
    saved_data = load_state()

    if saved_data is None:
        save_state(current_data)

        send_message(
            "✅ Мониторинг UZNF запущен.\n"
            "Жду публикации следующего торгового дня."
        )

        return

    if current_data["signature"] != saved_data["signature"]:

        message = (
            "📊 UZNF — London Stock Exchange\n\n"
            "🔔 Опубликованы итоги торгового дня\n\n"
            f"Цена открытия: {current_data['open']}\n"
            f"Цена закрытия: {current_data['close']}\n"
            f"Максимум: {current_data['high']}\n"
            f"Минимум: {current_data['low']}\n"
            f"Объём: {current_data['volume']}"
        )

        send_message(message)
        save_state(current_data)


if __name__ == "__main__":
    check_market_update()
