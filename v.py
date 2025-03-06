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

# 🔹 नॉर्मल यूजर के लिए कीबोर्ड
normal_user_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ I've Joined")]],
    resize_keyboard=True
)

# 🔹 एडमिन के लिए कीबोर्ड (सभी कमांड्स)
admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/total_users"), KeyboardButton(text="/active_users")],
        [KeyboardButton(text="/admin_list"), KeyboardButton(text="/broadcast")],
        [KeyboardButton(text="/approve"), KeyboardButton(text="/disapprove")],
        [KeyboardButton(text="/approved_users"), KeyboardButton(text="/server_status")],
        [KeyboardButton(text="/reset_user"), KeyboardButton(text="/user_info")],
        [KeyboardButton(text="/add_admin"), KeyboardButton(text="/remove_admin")],
        [KeyboardButton(text="/block_user"), KeyboardButton(text="/unblock_user")],
        [KeyboardButton(text="/blocked_users"), KeyboardButton(text="/unapproved_users")]
    ],
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
        await message.reply("🔹 Click below after joining:", reply_markup=normal_user_keyboard)
    else:
        if user_id in ADMINS:
            await message.reply("👑 **Welcome, Admin!** Use the commands below:", reply_markup=admin_keyboard)
        else:
            await message.reply("✅ You are verified! Now send me a file to check proxies.", reply_markup=normal_user_keyboard)

# 🔹 टोटल यूजर्स गिनने का कमांड
@dp.message(Command("total_users"))
async def total_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    total = len(users_data["users"])
    await message.reply(f"👥 **Total Users:** {total}")

# 🔹 एडमिन लिस्ट देखें
@dp.message(Command("admin_list"))
async def admin_list(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    admin_list = "\n".join(map(str, ADMINS)) or "No admins found."
    await message.reply(f"👑 **Admin List:**\n{admin_list}")

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

# 🔹 एडमिन कमांड्स
@dp.message(Command("approve"))
async def approve(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    user_id = int(message.text.split()[1])
    users_data["approved"].append(user_id)
    save_users(users_data)
    await message.reply(f"✅ User {user_id} approved for unlimited access!")

@dp.message(Command("block_user"))
async def block_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    user_id = int(message.text.split()[1])
    users_data["blocked"].append(user_id)
    save_users(users_data)
    await message.reply(f"🚫 User {user_id} has been blocked!")

@dp.message(Command("unblock_user"))
async def unblock_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    user_id = int(message.text.split()[1])
    users_data["blocked"].remove(user_id)
    save_users(users_data)
    await message.reply(f"✅ User {user_id} has been unblocked!")

# 🔹 सर्वर स्टेटस चेक करें
@dp.message(Command("server_status"))
async def server_status(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    import psutil, time
    uptime = time.time() - psutil.boot_time()
    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent

    await message.reply(f"🖥 **Server Status:**\n🔹 Uptime: {uptime:.2f} sec\n🔹 CPU Usage: {cpu_usage}%\n🔹 RAM Usage: {memory_usage}%")

# 🔹 बॉट स्टार्ट करें
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
