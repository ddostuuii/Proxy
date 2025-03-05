import os
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# 🔹 टेलीग्राम बॉट टोकन
BOT_TOKEN = "8018672833:AAEzaymr68hGginHA4uLbcc0moacOFxwO5c"

# 🔹 बॉट और डिस्पैचर सेटअप
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

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

# 🔹 /start कमांड हैंडलर
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("👋 Hello! Send me any **text file** (📄 `.txt`, `.csv`, `.log`, `.json`, etc.), and I will check proxies.")

# 🔹 जब यूज़र कोई फ़ाइल भेजे
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
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

    # 🔹 वर्किंग प्रॉक्सी भेजो (FSInputFile हटा कर `types.InputFile` यूज़ करो)
    if working_count > 0:
        await message.reply_document(types.InputFile(working_file))
    else:
        await message.reply("❌ No working proxies found!")

    # 🔹 खराब प्रॉक्सी भेजो
    if bad_count > 0:
        await message.reply_document(types.InputFile(bad_file))
    else:
        await message.reply("✅ All proxies are working!")

    # 🔹 क्लीनअप (पुरानी फ़ाइलें हटाएं)
    os.remove(file_path)
    os.remove(working_file)
    os.remove(bad_file)

# 🔹 बॉट स्टार्ट करें
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
