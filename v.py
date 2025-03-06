import os
import json
import asyncio
import requests
import psutil
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 🔹 बॉट टोकन और चैनल लिंक
BOT_TOKEN = "7612290520:AAHUwfiZdxhmZ-JhNqM6cDdXV9QCWkSm9fA"
CHANNEL_ID = -1002363906868
CHANNEL_LINK = "https://t.me/seedhe_maut"

# 🔹 एडमिन लिस्ट और यूजर डेटा फ़ाइल
ADMINS = [7017469802, 987654321]  # एडमिन की Telegram ID
USERS_DB = "users.json"

# 🔹 बॉट सेटअप
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# 🔹 जॉइन बटन वाला कीबोर्ड
sendKeyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ I've Joined")]],
    resize_keyboard=True
)

# 🔹 यूजर डेटा लोड/सेव करें
def load_users():
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f:
            return json.load(f)
    return {"users": [], "blocked": [], "approved": []}

def save_users(data):
    with open(USERS_DB, "w") as f:
        json.dump(data, f, indent=4)

users_data = load_users()

# 🔹 यूजर एड करें
def add_user(user_id):
    if user_id not in users_data["users"]:
        users_data["users"].append(user_id)
        save_users(users_data)

# 🔹 ब्लॉक/अनब्लॉक फंक्शन
def block_user(user_id):
    if user_id not in users_data["blocked"]:
        users_data["blocked"].append(user_id)
        save_users(users_data)

def unblock_user(user_id):
    if user_id in users_data["blocked"]:
        users_data["blocked"].remove(user_id)
        save_users(users_data)

# 🔹 यूजर अप्रूवल फंक्शन
def approve_user(user_id):
    if user_id not in users_data["approved"]:
        users_data["approved"].append(user_id)
        save_users(users_data)

def disapprove_user(user_id):
    if user_id in users_data["approved"]:
        users_data["approved"].remove(user_id)
        save_users(users_data)

# 🔹 चैनल जॉइन स्टेटस चेक करें
async def is_user_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# 🔹 /start कमांड
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    if user_id in users_data["blocked"]:
        await message.reply("🚫 You are blocked from using this bot.")
        return

    add_user(user_id)

    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)]])
        await message.reply("⚠ **Join our channel to use this bot!**", reply_markup=keyboard)
        await message.reply("🔹 Click below after joining:", reply_markup=sendKeyboard)
    else:
        await message.reply("✅ You are verified! Now send me a file to check proxies.")

# 🔹 "✅ I've Joined" बटन हैंडलर
@dp.message(lambda message: message.text == "✅ I've Joined")
async def check_join(message: types.Message):
    user_id = message.from_user.id

    if await is_user_member(user_id):
        await message.reply("✅ Thank you for joining! Now send me a file to check proxies.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.reply("❌ You haven't joined the channel yet!", reply_markup=sendKeyboard)

# 🔹 /total_users कमांड (सिर्फ एडमिन के लिए)
@dp.message(Command("total_users"))
async def total_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    total = len(users_data["users"])
    await message.reply(f"👥 **Total Users:** {total}")

# 🔹 /approve और /disapprove कमांड
@dp.message(Command("approve"))
async def approve(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        approve_user(user_id)
        await message.reply(f"✅ User {user_id} approved for unlimited access!")
    except:
        await message.reply("⚠ Usage: /approve <user_id>")

@dp.message(Command("disapprove"))
async def disapprove(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        disapprove_user(user_id)
        await message.reply(f"🚫 User {user_id} reverted to normal limit!")
    except:
        await message.reply("⚠ Usage: /disapprove <user_id>")

# 🔹 प्रॉक्सी चेकिंग फंक्शन
async def check_proxies(file_path, msg, max_proxies=None):
    with open(file_path, "r") as f:
        proxies = f.read().splitlines()

    if max_proxies:
        proxies = proxies[:max_proxies]

    working_proxies = []
    bad_proxies = []

    for proxy in proxies:
        try:
            response = requests.get("http://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.status_code == 200:
                working_proxies.append(proxy)
            else:
                bad_proxies.append(proxy)
        except:
            bad_proxies.append(proxy)

    working_file = "maut ✅.txt"
    bad_file = "maut ❌.txt"

    with open(working_file, "w") as f:
        f.write("\n".join(working_proxies))
    with open(bad_file, "w") as f:
        f.write("\n".join(bad_proxies))

    return working_file, bad_file, len(working_proxies), len(bad_proxies)

# 🔹 बॉट स्टार्ट करें
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
