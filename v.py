import os
import requests
import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 🔹 बॉट टोकन और चैनल लिंक
BOT_TOKEN = "7612290520:AAHUwfiZdxhmZ-JhNqM6cDdXV9QCWkSm9fA"
CHANNEL_ID = -1002363906868
CHANNEL_LINK = "https://t.me/seedhe_maut"

# 🔹 एडमिन और अप्रूव लिस्ट फ़ाइल
ADMINS = [7017469802, 987654321]  # एडमिन की Telegram ID डालें
USERS_DB = "users.json"

# 🔹 बॉट सेटअप
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# 🔹 Reply Keyboard
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
    except Exception:
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
# 🔹 टोटल यूजर्स गिनने का कमांड
@dp.message(Command("total_users"))
async def total_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    total = len(users_data["users"])
    await message.reply(f"👥 **Total Users:** {total}")

# 🔹 ब्रॉडकास्ट मैसेज भेजने का कमांड
@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.reply("⚠ Please provide a message to broadcast!")

    sent, failed = 0, 0
    for user_id in users_data["users"]:
        try:
            await bot.send_message(user_id, text)
            sent += 1
        except:
            failed += 1

    await message.reply(f"📢 **Broadcast Sent!**\n✅ Delivered: {sent}\n❌ Failed: {failed}")


# 🔹 जब यूज़र कोई फ़ाइल भेजे
@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    user_id = message.from_user.id

    if user_id in users_data["blocked"]:
        await message.reply("🚫 You are blocked from using this bot.")
        return

    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)]])
        await message.reply("⚠ **Join our channel first!**", reply_markup=keyboard)
        await message.reply("🔹 Click below after joining:", reply_markup=sendKeyboard)
        return

    file_id = message.document.file_id
    file_name = message.document.file_name

    allowed_formats = [".txt", ".csv", ".log", ".json"]
    if not any(file_name.endswith(ext) for ext in allowed_formats):
        await message.reply("⚠ Please send a valid text file (`.txt`, `.csv`, `.log`, `.json`).")
        return

    file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)
    file_info = await bot.get_file(file_id)
    await bot.download_file(file_info.file_path, file_path)

    msg = await message.reply("🔍 Checking proxies... Please wait.")

    # 🔹 अप्रूव और नॉर्मल यूजर लिमिट
    max_proxies = None if (user_id in ADMINS or user_id in users_data["approved"]) else 200
    working_file, bad_file, working_count, bad_count = await check_proxies(file_path, msg, max_proxies)

    await msg.edit_text(f"✅ Proxy checking completed!\n\n✅ **Working:** {working_count}\n❌ **Not Working:** {bad_count}")

    with open(working_file, "rb") as file:
        await message.reply_document(BufferedInputFile(file.read(), working_file))
    with open(bad_file, "rb") as file:
        await message.reply_document(BufferedInputFile(file.read(), bad_file))

    os.remove(file_path)
    os.remove(working_file)
    os.remove(bad_file)

# 🔹 एडमिन कमांड्स
@dp.message(Command("approve"))
async def approve(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    user_id = int(message.text.split()[1])
    approve_user(user_id)
    await message.reply(f"✅ User {user_id} approved for unlimited access!")

@dp.message(Command("disapprove"))
async def disapprove(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    user_id = int(message.text.split()[1])
    disapprove_user(user_id)
    await message.reply(f"🚫 User {user_id} reverted to normal limit!")

@dp.message(Command("approved_users"))
async def approved_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    approved_list = "\n".join(map(str, users_data["approved"])) or "No approved users."
    await message.reply(f"✅ **Approved Users:**\n{approved_list}")

# 🔹 बॉट स्टार्ट करें
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
