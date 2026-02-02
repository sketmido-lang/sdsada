import requests
import re
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from telegram import Bot
from telegram.ext import Application, CommandHandler
import asyncio
import urllib.parse

# Load environment variables
load_dotenv()
IVASMS_EMAIL = os.getenv("mohamed6mlak88@gmail.com")
IVASMS_PASSWORD = os.getenv("mando200909#")
BOT_TOKEN = os.getenv("8518091512:AAG4t1yXi2h-YDSE8Ktcmozpy5t7xDOq07E")
CHAT_ID = os.getenv("-1003576246424")

# Common headers
BASE_HEADERS = {
    "Host": "www.ivasms.com",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-GB,en;q=0.9",
    "Priority": "u=0, i",
    "Connection": "keep-alive"
}

async def send_to_telegram(sms):
    """Send SMS details to Telegram group with copiable number."""
    bot = Bot(token=BOT_TOKEN)
    message = (
        f"New SMS Received:\n"
        f"Timestamp: {sms['timestamp']}\n"
        f"Number: +{sms['number']}\n"
        f"Message: {sms['message']}\n"
        f"Range: {sms['range']}\n"
        f"Revenue: {sms['revenue']}"
    )
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Sent SMS to Telegram: {sms['message'][:50]}...")
    except Exception as e:
        print(f"Failed to send to Telegram: {str(e)}")

# Notification & sound are disabled for Railway
# def show_notification(number, message):
#     pass
# def play_notification_sound():
#     pass

# ... باقي الدوال payload_1 حتى parse_message كما هي بدون تعديل ...

async def start_command(update, context):
    """Handle /start command in Telegram."""
    await update.message.reply_text("IVASMS Bot started! Monitoring SMS statistics.")

async def main():
    """Main function to execute automation and monitor SMS statistics."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    today = datetime.now()
    from_date = today.strftime("%m/%d/%Y")
    to_date = (today + timedelta(days=1)).strftime("%m/%d/%Y")

    JSON_FILE = "sms_statistics.json"
    session_start = time.time()

    while True:
        try:
            with requests.Session() as session:
                tokens = payload_1(session)
                payload_2(session, tokens["_token"])
                response, csrf_token = payload_3(session)
                
                response = payload_4(session, csrf_token, from_date, to_date)
                ranges = parse_statistics(response.text)
                
                existing_ranges = load_from_json(JSON_FILE)
                existing_ranges_dict = {r["range_name"]: r for r in existing_ranges}

                if not existing_ranges:
                    save_to_json(ranges, JSON_FILE)

                while True:
                    if time.time() - session_start > 7200:
                        break

                    os.system('cls' if os.name == 'nt' else 'clear')

                    response = payload_4(session, csrf_token, from_date, to_date)
                    new_ranges = parse_statistics(response.text)
                    new_ranges_dict = {r["range_name"]: r for r in new_ranges}

                    for range_data in new_ranges:
                        range_name = range_data["range_name"]
                        current_count = range_data["count"]
                        existing_range = existing_ranges_dict.get(range_name)

                        if not existing_range:
                            response = payload_5(session, csrf_token, to_date, range_name)
                            numbers = parse_numbers(response.text)
                            for number_data in numbers[::-1]:
                                response = payload_6(session, csrf_token, to_date, number_data["number"], range_name)
                                message_data = parse_message(response.text)
                                sms = {
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "number": number_data["number"],
                                    "message": message_data["message"],
                                    "range": range_name,
                                    "revenue": message_data["revenue"]
                                }
                                print(f"New SMS: {sms}")
                                await send_to_telegram(sms)

                            existing_ranges.append(range_data)
                            existing_ranges_dict[range_name] = range_data

                        elif current_count > existing_range["count"]:
                            count_diff = current_count - existing_range["count"]
                            response = payload_5(session, csrf_token, to_date, range_name)
                            numbers = parse_numbers(response.text)
                            for number_data in numbers[-count_diff:][::-1]:
                                response = payload_6(session, csrf_token, to_date, number_data["number"], range_name)
                                message_data = parse_message(response.text)
                                sms = {
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "number": number_data["number"],
                                    "message": message_data["message"],
                                    "range": range_name,
                                    "revenue": message_data["revenue"]
                                }
                                print(f"New SMS: {sms}")
                                await send_to_telegram(sms)

                            for r in existing_ranges:
                                if r["range_name"] == range_name:
                                    r.update(range_data)
                                    break
                            existing_ranges_dict[range_name] = range_data

                    existing_ranges = new_ranges
                    existing_ranges_dict = new_ranges_dict
                    save_to_json(existing_ranges, JSON_FILE)

                    await asyncio.sleep(2 + (time.time() % 1))

        except Exception as e:
            print(f"Error: {str(e)}. Retrying in 30 seconds...")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
