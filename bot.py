import requests
import json
import os
import re
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")

URL = "https://www.londonstockexchange.com/stock/UZNF/national-investment-fund-of-the-republic-of-uzbekistan-jsc/company-page"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SUBSCRIBERS_FILE = "subscribers.json"
STATE_FILE = "state.json"


def send_message(chat_id, message):
    telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    requests.post(telegram_url, data=payload)


def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url).json()

    return response.get("result", [])


def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as file:
            return json.load(file)

    return []


def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as file:
        json.dump(subscribers, file)


def handle_subscriptions():
    subscribers = load_subscribers()
    updates = get_updates()

    for update in updates:
        if "message" not in update:
            continue

        message = update["message"]

        if "text" not in message:
            continue

        text = message["text"]
        chat_id = message["chat"]["id"]

        if text == "/start":
            if chat_id not in subscribers:
                subscribers.append(chat_id)
                save_subscribers(subscribers)

                send_message(
                    chat_id,
                    "✅ Вы подписались на UZNIF LSE Updates"
                )

        elif text == "/stop":
            if chat_id in subscribers:
                subscribers.remove(chat_id)
                save_subscribers(subscribers)

                send_message(
                    chat_id,
                    "❌ Вы отписались от обновлений"
                )


def extract_value(text, label):
    pattern = rf"{label}\s+([\d.,]+)"
    match = re.search(pattern, text)

    if match:
        return match.group(1)

    return "N/A"


def get_market_data():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    page_text = soup.get_text(" ", strip=True)

    open_price = extract_value(page_text, "Open")
    close_price = extract_value(page_text, "Previous close")
    high_price = extract_value(page_text, "High")
    low_price = extract_value(page_text, "Low")
    volume = extract_value(page_text, "Volume")

    signature = (
        f"{open_price}_{close_price}_{high_price}_{low_price}_{volume}"
    )

    return {
        "signature": signature,
        "open": open_price,
        "close": close_price,
        "high": high_price,
        "low": low_price,
        "volume": volume
    }


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)

    return None


def save_state(data):
    with open(STATE_FILE, "w") as file:
        json.dump(data, file)


def send_to_all(message):
    subscribers = load_subscribers()

    for chat_id in subscribers:
        send_message(chat_id, message)


def check_market_update():
    current_data = get_market_data()
    previous_data = load_state()

    if previous_data is None:
        save_state(current_data)
        return

    if current_data["signature"] != previous_data["signature"]:

        message = (
            "📊 UZNF — London Stock Exchange\n\n"
            "🔔 Опубликованы итоги торгового дня\n\n"
            f"Цена открытия: {current_data['open']}\n"
            f"Цена закрытия: {current_data['close']}\n"
            f"Максимум: {current_data['high']}\n"
            f"Минимум: {current_data['low']}\n"
            f"Объём: {current_data['volume']}"
        )

        send_to_all(message)
        save_state(current_data)


if __name__ == "__main__":
    handle_subscriptions()

    test_message = (
        "📊 UZNF — London Stock Exchange\n\n"
        "🔔 ТЕСТОВОЕ СООБЩЕНИЕ\n\n"
        "Цена открытия: 1250\n"
        "Цена закрытия: 1260\n"
        "Максимум: 1270\n"
        "Минимум: 1240\n"
        "Объём: 58240"
    )

    send_to_all(test_message)
