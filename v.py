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
       #usser info
@dp.message(Command("user_info"))
async def user_info(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        status = "Normal User"
        if user_id in users_data["blocked"]:
            status = "🚫 Blocked User"
        elif user_id in users_data["approved"]:
            status = "✅ Approved User"
        await message.reply(f"👤 **User ID:** {user_id}\n📌 **Status:** {status}")
    except:
        await message.reply("⚠ Usage: /user_info <user_id>")
# Bot Status
@dp.message(Command("bot_stats"))
async def bot_stats(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    total_users = len(users_data["users"])
    blocked_users = len(users_data["blocked"])
    approved_users = len(users_data["approved"])
    
    ram_usage = psutil.virtual_memory().percent
    cpu_usage = psutil.cpu_percent(interval=1)

    stats_text = f"""
📊 **Bot Statistics**
👥 **Total Users:** {total_users}
🚫 **Blocked Users:** {blocked_users}
✅ **Approved Users:** {approved_users}

🖥 **System Stats**
🔹 **RAM Usage:** {ram_usage}%
🔹 **CPU Usage:** {cpu_usage}%
"""
    await message.reply(stats_text)


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
    first_name = message.from_user.first_name  

    if user_id in users_data["blocked"]:
        await message.reply("🚫 You are blocked from using this bot.")
        return

    add_user(user_id)

    welcome_text = f"""
👋 **Welcome, {first_name}!**  
I'm your Proxy Checker Bot. 🚀  

📌 *With me, you can:*  
- ✅ Check proxies  
- 📊 View bot statistics  
- ⚙ Manage users (Admins Only)  

🔹 **To get started:**  
1️⃣ *Join our channel:* [Seedhe Maut]({CHANNEL_LINK})  
2️⃣ *Then press the button below:*  
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
    ])

    await message.reply(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(lambda call: call.data == "check_join")
async def check_join_callback(call: types.CallbackQuery):
    user_id = call.from_user.id

    if await is_user_member(user_id):
        await call.message.edit_text("✅ Thank you for joining! Now send me a file to check proxies.")
    else:
        await call.answer("❌ You haven't joined the channel yet!", show_alert=True)

        
        #brodcast
user_warnings = {}  # वॉर्निंग स्टोर करने के लिए
user_limits = {}  # यूज़र्स की लिमिट स्टोर करने के लिए

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        return await message.reply("⚠ Usage: /broadcast <message>")

    count = 0
    for user_id in users_data["users"]:
        try:
            await bot.send_message(user_id, f"📢 **Broadcast:**\n\n{text}")
            count += 1
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")

    await message.reply(f"✅ Broadcast sent to {count} users!")

@dp.message(Command("warnings"))
async def view_warnings(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        warnings = user_warnings.get(user_id, [])

        if not warnings:
            return await message.reply(f"✅ User {user_id} has no warnings.")

        warnings_list = "\n".join([f"⚠ {w}" for w in warnings])
        await message.reply(f"🚨 **Warnings for {user_id}:**\n\n{warnings_list}")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /warnings <user_id>")

@dp.message(Command("warn"))
async def warn_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        _, user_id, reason = message.text.split(maxsplit=2)
        user_id = int(user_id)

        if user_id not in user_warnings:
            user_warnings[user_id] = []
        user_warnings[user_id].append(reason)

        await message.reply(f"⚠ **User {user_id} warned for:** {reason}")
        await bot.send_message(user_id, f"⚠ **Warning:** {reason}")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /warn <user_id> <reason>")

@dp.message(Command("set_limit"))
async def set_limit(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        _, user_id, limit = message.text.split()
        user_id, limit = int(user_id), int(limit)
        user_limits[user_id] = limit
        await message.reply(f"✅ User {user_id} की प्रॉक्सी लिमिट {limit} सेट कर दी गई!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /set_limit <user_id> <limit>")

@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        if user_id in users_data["users"]:
            users_data["users"].remove(user_id)
        if user_id not in users_data["blocked"]:
            users_data["blocked"].append(user_id)

        save_users(users_data)
        await message.reply(f"🚨 User {user_id} has been permanently banned!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /ban <user_id>")

@dp.message(Command("unban"))
async def unban_user(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        if user_id in users_data["blocked"]:
            users_data["blocked"].remove(user_id)
        if user_id not in users_data["users"]:
            users_data["users"].append(user_id)

        save_users(users_data)
        await message.reply(f"✅ User {user_id} has been unbanned!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /unban <user_id>")
@dp.message(Command("help"))
async def help_command(message: types.Message):
    commands_text = """
🤖 *Bot Commands*:

🔹 *General Commands:*
`/start` \\- Start the bot  
`/help` \\- Show all available commands  
`/total_users` \\- View total users  

👑 *Admin Commands:*
`/add_admin <user_id>` \\- Add a new admin  
`/remove_admin <user_id>` \\- Remove an admin  
`/list_admins` \\- View all admins  
`/approve <user_id>` \\- Grant unlimited access to a user  
`/disapprove <user_id>` \\- Reset user to normal limit  
`/block <user_id>` \\- Block a user  
`/unblock <user_id>` \\- Unblock a user  
`/ban <user_id>` \\- Permanently ban a user  
`/unban <user_id>` \\- Remove a user's ban  
`/set_limit <user_id> <limit>` \\- Set proxy checking limit for a user  
`/warn <user_id> <reason>` \\- Warn a user  
`/warnings <user_id>` \\- View a user's warnings  
`/active_users` \\- View active users  
`/broadcast <message>` \\- Send a message to all users  
`/restart_bot` \\- Restart the bot  

🛠 *Proxy Checking Commands:*
`/check_proxies` \\- Check proxies  
`/upload_valid` \\- Upload valid proxy file  
`/upload_invalid` \\- Upload invalid proxy file  

ℹ️ *For any bot\\-related questions, contact an admin\\.*
    """
    
    await message.reply(commands_text, parse_mode="MarkdownV2")



@dp.message(Command("total_users"))
async def total_users(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    total = len(users_data["users"])
    await message.reply(f"👥 **Total Users:** {total}")

@dp.message(Command("approve"))
async def approve(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        approve_user(user_id)
        await message.reply(f"✅ User {user_id} approved for unlimited access!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /approve <user_id>")

@dp.message(Command("disapprove"))
async def disapprove(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.reply("🚫 You are not an admin!")

    try:
        user_id = int(message.text.split()[1])
        disapprove_user(user_id)
        await message.reply(f"🚫 User {user_id} reverted to normal limit!")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("⚠ Usage: /disapprove <user_id>")
# 🔹 प्रॉक्सी फ़ाइल हैंडलर (अपडेटेड)
@dp.message(lambda message: message.document)
async def handle_proxy_file(message: types.Message):
    user_id = message.from_user.id

    # 🔹 ब्लॉक चेक
    if user_id in users_data["blocked"]:
        return await message.reply("🚫 You are blocked from using this bot.")

    # 🔹 चैनल जॉइन चेक करें
    if not await is_user_member(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
        ])
        return await message.reply("❌ You must join the channel to use this bot!", reply_markup=keyboard)

    # 🔹 यूजर अप्रूवल और लिमिट चेक करें
    max_proxies = None
    if user_id not in users_data["approved"]:
        max_proxies = 200  # नॉर्मल यूज़र्स के लिए लिमिट

    # 🔹 फ़ाइल डाउनलोड करें
    file_id = message.document.file_id
    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path
    file_name = "uploaded_proxies.txt"

    await bot.download_file(file_path, file_name)

    await message.reply("⏳ Checking proxies, please wait...")

    # 🔹 प्रॉक्सी चेक करें
    working_file, bad_file, good_count, bad_count = await check_proxies(file_name, message, max_proxies)

    # 🔹 यूज़र को रिज़ल्ट भेजें
    await message.reply(f"✅ **Proxy Check Completed!**\n\n🔹 Working: {good_count}\n🔹 Bad: {bad_count}")

    # 🔹 वर्किंग और बैड प्रॉक्सी फ़ाइल भेजें
    if good_count > 0:
        await message.reply_document(BufferedInputFile(open(working_file, "rb").read(), filename="maut ✅.txt"))
    if bad_count > 0:
        await message.reply_document(BufferedInputFile(open(bad_file, "rb").read(), filename="maut ❌.txt"))

    # 🔹 प्रॉक्सी चेक करें
    working_file, bad_file, good_count, bad_count = await check_proxies(file_name, message, max_proxies)

    # 🔹 यूज़र को रिज़ल्ट भेजें
    await message.reply(f"✅ **Proxy Check Completed!**\n\n🔹 Working: {good_count}\n🔹 Bad: {bad_count}")

    # 🔹 वर्किंग और बैड प्रॉक्सी फ़ाइल भेजें
    await message.reply_document(BufferedInputFile(open(working_file, "rb").read(), filename="maut ✅.txt"))
    await message.reply_document(BufferedInputFile(open(bad_file, "rb").read(), filename="maut ❌.txt"))


# 🔹 प्रॉक्सी चेकिंग फंक्शन (अपडेटेड)
async def check_proxies(file_path, message, max_proxies=None):
    with open(file_path, "r") as f:
        proxies = f.read().splitlines()

    if max_proxies:
        proxies = proxies[:max_proxies]

    working_proxies = []
    bad_proxies = []
    total = len(proxies)

    progress_msg = await message.reply(f"🔄 Checking {total} proxies... Please wait.")

    for index, proxy in enumerate(proxies, start=1):
        proxy_msg = await message.reply(f"🔍 Checking: `{proxy}`...")

        try:
            response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.status_code == 200:
                working_proxies.append(proxy)
                await proxy_msg.edit_text(f"✅ **Working**\n🔹 Proxy: `{proxy}`\n🔹 Checked by maut @seedhe_maut_bot")
            else:
                bad_proxies.append(proxy)
                await proxy_msg.edit_text(f"❌ **Not Working**\n🔹 Proxy: `{proxy}`\n🔹 Checked by maut @seedhe_maut_bot")
        except:
            bad_proxies.append(proxy)
            await proxy_msg.edit_text(f"❌ **Not Working**\n🔹 Proxy: `{proxy}`\n🔹 Checked by maut @seedhe_maut_bot")

        # 🔹 अपडेटेड प्रोग्रेस मैसेज
        if index % 5 == 0 or index == total:
            await progress_msg.edit_text(f"✅ Checked: {index}/{total}\n✔️ Working: {len(working_proxies)}\n❌ Bad: {len(bad_proxies)}")

    working_file = "maut ✅.txt"
    bad_file = "maut ❌.txt"

    with open(working_file, "w") as f:
        f.write("\n".join(working_proxies) if working_proxies else "No working proxies found.")
    with open(bad_file, "w") as f:
        f.write("\n".join(bad_proxies) if bad_proxies else "No bad proxies found.")

    return working_file, bad_file, len(working_proxies), len(bad_proxies)



# 🔹 बॉट स्टार्ट करें
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
