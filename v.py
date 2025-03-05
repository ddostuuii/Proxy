import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# 🔹 टेलीग्राम बॉट टोकन और चैनल लिंक
BOT_TOKEN = "7612290520:AAHUwfiZdxhmZ-JhNqM6cDdXV9QCWkSm9fA"  # अपना बॉट टोकन डालें
CHANNEL_LINK = "https://t.me/+R4ram7JA-yY4MWQ1"  # चैनल इन्वाइट लिंक

# 🔹 नया तरीका Aiogram v3.7+ के लिए
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# 🔹 बॉट खुद पता लगाएगा कि वह किस चैनल में एडमिन है
async def get_admin_channel():
    try:
        admins = await bot.get_chat_administrators(CHANNEL_LINK)
        return admins[0].chat.id if admins else None
    except Exception:
        return None

# 🔹 चैनल जॉइन चेक करने का फ़ंक्शन
async def is_user_member(user_id):
    channel_id = await get_admin_channel()
    if not channel_id:
        return True  # अगर बॉट चैनल नहीं ढूंढ पाया, तो चेक स्किप करो
    try:
        member = await bot.get_chat_member(channel_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# 🔹 /start कमांड हैंडलर (चेक करेगा कि यूजर चैनल में है या नहीं)
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
            ]
        )
        await message.reply("⚠ **To use this bot, please join our channel first!**", reply_markup=keyboard)
        return

    # 🔹 अगर यूजर पहले से जॉइन है
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/seedhe_maut_bot")]
        ]
    )
    await message.reply("👋 Hello! Send me any **text file** (📄 `.txt`, `.csv`, `.log`, `.json`, etc.), and I will check proxies.", reply_markup=keyboard)

# 🔹 "I've Joined" बटन हैंडलर (यूजर ने चैनल जॉइन किया या नहीं)
@dp.callback_query(lambda call: call.data == "check_join")
async def check_join(call: types.CallbackQuery):
    user_id = call.from_user.id
    if await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="👨‍💻 Developer", url="https://t.me/seedhe_maut_bot")]
            ]
        )
        await call.message.edit_text("✅ Thank you for joining! Now send me a **text file** with proxies.", reply_markup=keyboard)
    else:
        await call.answer("❌ You haven't joined the channel yet!", show_alert=True)

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
    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
            ]
        )
        await message.reply("⚠ **To use this bot, please join our channel first!**", reply_markup=keyboard)
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

# 🔹 बॉट स्टार्ट करने का नया तरीका (Aiogram v3.7+)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
