import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 🔹 टेलीग्राम बॉट टोकन और चैनल लिंक
BOT_TOKEN = "7612290520:AAHUwfiZdxhmZ-JhNqM6cDdXV9QCWkSm9fA"  # अपना बॉट टोकन डालें
CHANNEL_ID = -1002363906868  # अपने चैनल का ID डालें
CHANNEL_LINK = "https://t.me/seedhe_maut"  # चैनल का इन्वाइट लिंक

# 🔹 बॉट सेटअप
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# 🔹 वेरिफाइड यूज़र्स की लिस्ट (RAM में स्टोर)
verified_users = set()

# 🔹 यूजर चैनल में जॉइन है या नहीं
async def is_user_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# 🔹 /start कमांड (चैनल जॉइन चेक + /maut बटन हाइड)
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    if user_id in verified_users:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/maut")]],
            resize_keyboard=True
        )
        await message.reply("✅ You are already verified! Click `/maut` to check proxies.", reply_markup=keyboard)
        return

    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
            ]
        )
        await message.reply("⚠ **To use this bot, please join our channel first!**", reply_markup=keyboard)
    else:
        verified_users.add(user_id)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/maut")]],
            resize_keyboard=True
        )
        await message.reply("✅ You are verified! Click `/maut` to check proxies.", reply_markup=keyboard)

# 🔹 "I've Joined" बटन हैंडलर (अब `/maut` दिखेगा)
@dp.callback_query(lambda call: call.data == "check_join")
async def check_join(call: types.CallbackQuery):
    user_id = call.from_user.id

    if await is_user_member(user_id):
        verified_users.add(user_id)
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/maut")]],
            resize_keyboard=True
        )
        await call.message.edit_text("✅ Thank you for joining! Now click `/maut` to check proxies.", reply_markup=keyboard)
    else:
        await call.answer("❌ You haven't joined the channel yet!", show_alert=True)

# 🔹 `/maut` तभी चलेगा जब यूजर वेरिफाइड होगा
@dp.message(Command("maut"))
async def maut(message: types.Message):
    user_id = message.from_user.id

    if user_id not in verified_users:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
            ]
        )
        await message.reply("⚠ **You must join our channel first!**", reply_markup=keyboard)
        return

    await message.reply("👋 Hello! Send me any **text file** (📄 `.txt`, `.csv`, `.log`, `.json`, etc.), and I will check proxies.")

# 🔹 प्रॉक्सी चेक करने का फ़ंक्शन
async def check_proxies(file_path, message):
    timeout = 5
    working_proxies = []
    bad_proxies = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        proxies = file.read().splitlines()

    total_proxies = len(proxies)
    checked_count = 0

    for proxy in proxies:
        proxy = proxy.strip()
        if not proxy:
            continue  

        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxy_dict, timeout=timeout)
            if response.status_code == 200:
                working_proxies.append(proxy)
            else:
                bad_proxies.append(proxy)
        except requests.RequestException:
            bad_proxies.append(proxy)

        checked_count += 1

        # 🔹 हर 5 प्रॉक्सी के बाद अपडेट भेजो
        if checked_count % 5 == 0 or checked_count == total_proxies:
            await message.edit_text(f"🔄 Checking Proxies...\n✅ Working: {len(working_proxies)}\n❌ Not Working: {len(bad_proxies)}\n⏳ Total Checked: {checked_count}/{total_proxies}")

        await asyncio.sleep(0.5)  

    # 🔹 रिजल्ट फाइल बनाएं
    working_file = "maut ✅.txt"
    bad_file = "maut ❌.txt"

    with open(working_file, "w") as wf:
        wf.write("\n".join(working_proxies))

    with open(bad_file, "w") as bf:
        bf.write("\n".join(bad_proxies))

    return working_file, bad_file, len(working_proxies), len(bad_proxies)

# 🔹 जब यूज़र कोई फ़ाइल भेजे
@dp.message(lambda message: message.document)
async def handle_document(message: types.Message):
    user_id = message.from_user.id

    if user_id not in verified_users:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
            ]
        )
        await message.reply("⚠ **You must join our channel first!**", reply_markup=keyboard)
        return

    file_id = message.document.file_id
    file_name = message.document.file_name

    # 🔹 सपोर्टेड टेक्स्ट फॉर्मेट्स
    allowed_formats = [".txt", ".csv", ".log", ".json"]
    
    if not any(file_name.endswith(ext) for ext in allowed_formats):
        await message.reply("⚠ Please send a **valid text file** (`.txt`, `.csv`, `.log`, `.json`).")
        return

    # 🔹 फ़ाइल डाउनलोड करें
    file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)
    
    file_info = await bot.get_file(file_id)
    await bot.download_file(file_info.file_path, file_path)

    msg = await message.reply("🔍 Checking proxies... Please wait.")

    # 🔹 प्रॉक्सी चेक करें (प्रॉसेसिंग स्क्रीन दिखाते हुए)
    working_file, bad_file, working_count, bad_count = await check_proxies(file_path, msg)

    # 🔹 फाइनल रिजल्ट भेजें
    await msg.edit_text(f"✅ Proxy checking completed!\n\n✅ **Working:** {working_count}\n❌ **Not Working:** {bad_count}")

    # 🔹 वर्किंग प्रॉक्सी भेजो
    if working_count > 0:
        with open(working_file, "rb") as file:
            await message.reply_document(BufferedInputFile(file.read(), working_file))
    else:
        await message.reply("❌ No working proxies found!")

    # 🔹 खराब प्रॉक्सी भेजो
    if bad_count > 0:
        with open(bad_file, "rb") as file:
            await message.reply_document(BufferedInputFile(file.read(), bad_file))
    else:
        await message.reply("✅ All proxies are working!")

    # 🔹 क्लीनअप (पुरानी फ़ाइलें हटाएं)
    os.remove(file_path)
    os.remove(working_file)
    os.remove(bad_file)

# 🔹 बॉट स्टार्ट करने का तरीका
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
