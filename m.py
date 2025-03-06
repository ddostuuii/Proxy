import random
import os
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler, ContextTypes

# Bot States
AWAITING_QUANTITY = 1

# Channel Info
CHANNEL_ID = -1002363906868  # Your Channel ID
CHANNEL_LINK = "https://t.me/seedhe_maut"  # Your Channel Link

# Blocked Users Data
users_data = {"blocked": set()}

# Function to Check if User is in the Channel
async def is_user_member(user_id, context):
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    first_name = update.message.from_user.first_name  

    if user_id in users_data["blocked"]:
        await update.message.reply_text("🚫 You are blocked from using this bot.")
        return

    # Check if User is a Member of the Channel
    is_member = await is_user_member(user_id, context)

    if not is_member:
        welcome_text = f"""
🚨 **You must join our channel to use this bot!**  
🔹 **Join here:** [Seedhe Maut]({CHANNEL_LINK})  

Then press the button below to verify. ✅
"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔹 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ I've Joined", callback_data="check_join")]
        ])

        await update.message.reply_text(welcome_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # If User is Already a Member
    welcome_text = f"""
👋 **Welcome, {first_name}!**  
I'm your Card Generator Bot. 💳  

📌 *With me, you can:*  
- 🔹 Generate random cards  
- 🔢 Customize card details (MM/YY/CVV)  
- 📂 Download bulk generated cards  
"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Button Handler to Verify Channel Join
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    is_member = await is_user_member(user_id, context)

    if is_member:
        await query.message.edit_text("✅ Verification successful! You can now use the bot.")
    else:
        await query.answer("❌ You haven't joined the channel yet!", show_alert=True)

# Function to Generate a Card
def generate_card(user_input):
    parts = user_input.split('|')

    card_start = parts[0]
    remaining_digits = 16 - len(card_start)
    card_number = card_start + ''.join(str(random.randint(0, 9)) for _ in range(remaining_digits))

    exp_month = str(random.randint(1, 12)).zfill(2)
    exp_year = str(random.randint(25, 35))
    cvv = str(random.randint(100, 999))

    if len(parts) > 1 and parts[1].isdigit():
        if len(parts[1]) == 2:  
            exp_month = parts[1]
        elif len(parts[1]) == 4:  
            exp_month, exp_year = parts[1][:2], parts[1][2:]
        elif len(parts[1]) == 3:  
            cvv = parts[1]

    if len(parts) > 2 and parts[2].isdigit():
        if len(parts[2]) == 2:  
            exp_year = parts[2]
        elif len(parts[2]) == 3:  
            cvv = parts[2]

    if len(parts) > 3 and parts[3].isdigit() and len(parts[3]) == 3:  
        cvv = parts[3]

    return f"{card_number}|{exp_month}|{exp_year}|{cvv}"

# /gen Command Handler
async def gen_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    args = context.args

    if not args:
        await update.message.reply_text("❌ Invalid format! Use: `/gen 37377` or `/gen 37377|MMYY|CVV`")
        return ConversationHandler.END

    user_input = args[0].strip()

    if not all(part.isdigit() for part in user_input.split('|')):
        await update.message.reply_text("❌ Invalid input! Please enter a valid card prefix.")
        return ConversationHandler.END

    context.user_data['prefix'] = user_input
    await update.message.reply_text("📊 How many cards do you want to generate? (Enter a number between 1-1000)")
    return AWAITING_QUANTITY

# Generate and Send Cards
async def generate_cards(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        num_cards = int(update.message.text.strip())
        if num_cards < 1 or num_cards > 1000:
            await update.message.reply_text("❌ Please enter a number between 1 and 1000.")
            return AWAITING_QUANTITY

        user_input = context.user_data['prefix']
        cards = [generate_card(user_input) for _ in range(num_cards)]

        if num_cards <= 30:
            await update.message.reply_text(f"✅ Generated {num_cards} Cards:\n```\n" + "\n".join(cards) + "\n```", parse_mode='Markdown')
        else:
            file_path = "generated_cards.txt"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(cards))

            with open(file_path, "rb") as file:
                await update.message.reply_document(document=InputFile(file, filename="generated_cards.txt"))

            os.remove(file_path)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid number! Please enter a valid quantity.")
        return AWAITING_QUANTITY

    return ConversationHandler.END

# Bot Setup
def main():
    TOKEN = "7611262857:AAH-9-K_C8Vp3QNtQ9_C1UIIKAR2pWn70u4"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("gen", gen_handler)],
        states={
            AWAITING_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_cards)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
