import sqlite3
import requests
import telebot
from telebot import types

# ================= CONFIGURATION =================
BOT_TOKEN = "8716459674:AAEMnn2l8XnthsD5rursGJqljbaoD1lxvF4"
ADMIN_ID = 8023293047

# Payment Details
UPI_ID = "9798981367@ybl"
UPI_NAME = "SMM Store"

# SMM Panel API Config
SMM_API_URL = "https://smmfollows.com/api/v2"
SMM_API_KEY = "ade40acb28ee63e075df9e965b92e01e"

# Support Username
SUPPORT_USERNAME = "@techhasir"

# Services Mapping (Views + Followers + Likes sabhi add ho gayi hain)
SERVICE_RATES = {
    # --- Instagram Views ---
    "19129": {"name": "IG Views (Instant)", "rate_per_1k": 1.0},
    "19130": {"name": "IG Video Views", "rate_per_1k": 25.0},
    "19131": {"name": "IG Video Views + Reach", "rate_per_1k": 32.0},
    "19132": {"name": "IG Story Views", "rate_per_1k": 12.0},

    # --- Instagram Followers (Updates & Stable) ---
    "19405": {"name": "IG Followers (High Quality - No Refill)", "rate_per_1k": 150.0},
    "19406": {"name": "IG Followers (Fast 5-7K/hr - No Refill)", "rate_per_1k": 210.0},
    "19407": {"name": "IG Followers (Super Fast 5-10K/hr)", "rate_per_1k": 510.0},
    "19425": {"name": "IG Followers (Real Accounts - Low Drop)", "rate_per_1k": 195.0},
    "19426": {"name": "IG Followers (30 Days Refill)", "rate_per_1k": 360.0},
    "19427": {"name": "IG Followers (90 Days Refill)", "rate_per_1k": 399.0},
    "19428": {"name": "IG Followers (365 Days Refill)", "rate_per_1k": 410.0},

    # --- Instagram Likes ---
    "18985": {"name": "IG Likes (Real - 30 Days Refill)", "rate_per_1k": 12.0},
    "18986": {"name": "IG Likes (HQ Profiles - 30 Days Refill)", "rate_per_1k": 14.0},
    "14182": {"name": "IG Likes (100% Profile Pictures - No Refill)", "rate_per_1k": 34.0},
    "18987": {"name": "IG Likes (Old Accounts - 365 Days Refill)", "rate_per_1k": 40.0}
}
# =================================================

bot = telebot.TeleBot(BOT_TOKEN)

user_payments = {}
user_orders = {}

def init_db():
    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, 
            balance REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            smm_order_id TEXT,
            service_id TEXT,
            link TEXT,
            quantity INTEGER,
            charge REAL,
            status TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            txn_id TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id):
    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

def update_user_balance(user_id, amount):
    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def save_order(user_id, smm_order_id, service_id, link, quantity, charge, status="Success"):
    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (user_id, smm_order_id, service_id, link, quantity, charge, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, str(smm_order_id), service_id, link, quantity, charge, status))
    conn.commit()
    conn.close()

def send_smm_order(service_id, link, quantity):
    payload = {
        "key": SMM_API_KEY, 
        "action": "add", 
        "service": service_id, 
        "link": link, 
        "quantity": quantity
    }
    try:
        response = requests.post(SMM_API_URL, data=payload, timeout=15)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🚀 New Order"),
        types.KeyboardButton("📋 Services"),
        types.KeyboardButton("👤 Profile / Balance"),
        types.KeyboardButton("💳 Add Funds"),
        types.KeyboardButton("📞 Support")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    get_user_balance(message.from_user.id)
    bot.send_message(
        message.chat.id,
        f"👋 Welcome {message.from_user.first_name}!\nServices order karne ke liye neeche diye gaye buttons use karein.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda msg: msg.text == "👤 Profile / Balance")
def profile_handler(message):
    balance = get_user_balance(message.from_user.id)
    bot.send_message(message.chat.id, f"🆔 User ID: `{message.from_user.id}`\n💰 Balance: ₹{balance:.2f}", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📋 Services")
def services_handler(message):
    text = "📋 *Available Services List:*\n\n"
    for s_id, s_info in SERVICE_RATES.items():
        text += f"🔹 ID `{s_id}`: {s_info['name']} (₹{s_info['rate_per_1k']}/1k)\n"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📞 Support")
def support_handler(message):
    bot.send_message(message.chat.id, f"📞 Kisi bhi query ya issue ke liye sampark karein:\n👉 {SUPPORT_USERNAME}")

# ==================== MANUAL PAYMENT SYSTEM ====================

@bot.message_handler(func=lambda msg: msg.text == "💳 Add Funds")
def add_funds_start(message):
    text = (
        "💳 *Add Funds (Manual Payment)*\n\n"
        f"🔹 **UPI ID:** `{UPI_ID}`\n"
        f"🔹 **Name:** {UPI_NAME}\n\n"
        "📌 *Steps:*\n"
        "1. Upar di gayi UPI ID par payment karein.\n"
        "2. Payment karne ke baad, **kitna amount pay kiya** wo yahan enter karein (e.g. `100`):"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(message, process_payment_amount)

def process_payment_amount(message):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Kripya valid amount enter karein. Dobara '💳 Add Funds' dabayein.")
        return

    user_payments[message.from_user.id] = {"amount": amount}
    bot.send_message(message.chat.id, "Ab payment ka **UTR / Transaction ID** ya reference number enter karein:")
    bot.register_next_step_handler(message, process_payment_txn)

def process_payment_txn(message):
    uid = message.from_user.id
    txn_id = message.text.strip()
    pay_data = user_payments.get(uid)

    if not pay_data:
        bot.send_message(message.chat.id, "Session expire ho gaya. Dobara try karein.")
        return

    amount = pay_data["amount"]

    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO payments (user_id, amount, txn_id) VALUES (?, ?, ?)", (uid, amount, txn_id))
    payment_db_id = cursor.lastrowid
    conn.commit()
    conn.close()

    bot.send_message(
        message.chat.id, 
        f"✅ Aapki payment request submit ho gayi hai!\n"
        f"Amount: ₹{amount:.2f}\n"
        f"Txn ID: `{txn_id}`\n\n"
        f"Admin verification ke baad balance aapke wallet me add ho jayega.",
        parse_mode="Markdown"
    )

    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("Approve ✅", callback_data=f"pay_app_{payment_db_id}")
    btn_reject = types.InlineKeyboardButton("Reject ❌", callback_data=f"pay_rej_{payment_db_id}")
    markup.add(btn_approve, btn_reject)

    admin_alert = (
        "🔔 *New Deposit Request!*\n\n"
        f"👤 User: {message.from_user.first_name} (`{uid}`)\n"
        f"💰 Amount: ₹{amount:.2f}\n"
        f"🧾 UTR / Txn ID: `{txn_id}`\n"
        f"🆔 Request ID: `{payment_db_id}`"
    )
    bot.send_message(ADMIN_ID, admin_alert, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('pay_app_', 'pay_rej_')))
def handle_payment_actions(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Aap authorized nahi hain.")
        return

    action, req_id = call.data.split("_")[1], int(call.data.split("_")[2])

    conn = sqlite3.connect("smm_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, txn_id, status FROM payments WHERE id = ?", (req_id,))
    row = cursor.fetchone()

    if not row:
        bot.answer_callback_query(call.id, "Request nahi mili.")
        conn.close()
        return

    user_id, amount, txn_id, status = row

    if status != "PENDING":
        bot.answer_callback_query(call.id, f"Yeh request pehle hi {status} ho chuki hai.")
        conn.close()
        return

    if action == "app":
        cursor.execute("UPDATE payments SET status = 'APPROVED' WHERE id = ?", (req_id,))
        conn.commit()
        conn.close()

        update_user_balance(user_id, amount)

        bot.edit_message_text(
            f"✅ *Approved!* Request #{req_id}\nUser `{user_id}` ko ₹{amount:.2f} add ho gaye.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        bot.send_message(user_id, f"🎉 *Deposit Success!*\nAapke account me ₹{amount:.2f} add kar diye gaye hain.", parse_mode="Markdown")

    elif action == "rej":
        cursor.execute("UPDATE payments SET status = 'REJECTED' WHERE id = ?", (req_id,))
        conn.commit()
        conn.close()

        bot.edit_message_text(
            f"❌ *Rejected!* Request #{req_id} for User `{user_id}`.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        bot.send_message(user_id, f"⚠️ Aapki ₹{amount:.2f} (Txn: `{txn_id}`) ki deposit request reject kar di gayi hai.", parse_mode="Markdown")

# ==================== ORDER FLOW ====================

@bot.message_handler(func=lambda msg: msg.text == "🚀 New Order")
def new_order_start(message):
    bot.send_message(message.chat.id, "Service ID enter karein:")
    bot.register_next_step_handler(message, process_service_id)

def process_service_id(message):
    service_id = message.text.strip()
    if service_id not in SERVICE_RATES:
        bot.send_message(message.chat.id, "❌ Invalid Service ID. '📋 Services' list se ID dekhkar dalein.")
        return
    user_orders[message.from_user.id] = {"service_id": service_id}
    bot.send_message(message.chat.id, "🔗 Target link send karein:")
    bot.register_next_step_handler(message, process_link)

def process_link(message):
    user_orders[message.from_user.id]["link"] = message.text.strip()
    bot.send_message(message.chat.id, "🔢 Quantity enter karein:")
    bot.register_next_step_handler(message, process_quantity)

def process_quantity(message):
    try:
        qty = int(message.text.strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(message.chat.id, "❌ Valid number enter karein.")
        return

    uid = message.from_user.id
    order = user_orders.get(uid)
    if not order:
        bot.send_message(message.chat.id, "Session expire ho gaya.")
        return

    cost = (qty / 1000) * SERVICE_RATES[order["service_id"]]["rate_per_1k"]
    bal = get_user_balance(uid)

    if bal < cost:
        bot.send_message(message.chat.id, f"❌ Insufficient Balance!\nChahiye: ₹{cost:.2f}\nAapka Balance: ₹{bal:.2f}")
        return

    res = send_smm_order(order["service_id"], order["link"], qty)
    if "order" in res:
        update_user_balance(uid, -cost)
        save_order(uid, res["order"], order["service_id"], order["link"], qty, cost, status="Success")
        bot.send_message(message.chat.id, f"✅ Order Placed! ID: `{res['order']}`\nCost: ₹{cost:.2f}", parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"⚠️ Error: {res.get('error', 'Failed')}")

print("Bot is running...")
bot.infinity_polling()
