# ربات فروش کانفیگ دستی - نسخه کامل با پنل ادمین تعاملی
# مناسب برای Railway / GitHub

import telebot
from telebot.apihelper import ApiTelegramException
from telebot import types
import time
import json
import os
from datetime import datetime
import re

# ============ تنظیمات ============
TOKEN = "8262116870:AAESTHjD7Vhph5EGRhBqV_2lHpuQ5tI5LnQ"
CHANNEL_USERNAME = '@janti_1306'
MAIN_ADMIN_ID = 6443963679  # ادمین اصلی

# ============ توابع ذخیره‌سازی ============
DATA_DIR = os.environ.get('DATA_DIR', '/tmp')

def get_data_file_path(filename):
    return os.path.join(DATA_DIR, filename)

def load_users():
    filename = get_data_file_path('users.json')
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    filename = get_data_file_path('users.json')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def load_products():
    filename = get_data_file_path('products.json')
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_products(products):
    filename = get_data_file_path('products.json')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def load_admins():
    filename = get_data_file_path('admins.json')
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return [MAIN_ADMIN_ID]
    return [MAIN_ADMIN_ID]

def save_admins(admins):
    filename = get_data_file_path('admins.json')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(admins, f, ensure_ascii=False, indent=4)

def load_settings():
    filename = get_data_file_path('settings.json')
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    filename = get_data_file_path('settings.json')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def load_broadcast_log():
    filename = get_data_file_path('broadcast_log.json')
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_broadcast_log(log):
    filename = get_data_file_path('broadcast_log.json')
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=4)

# ============ توابع کاربر ============
def ensure_user_fields(user_data):
    defaults = {
        'referral_count': 0,
        'referrals': [],
        'referred_by': None,
        'pending_3_reward': False,
        'claimed_3': False,
        'reward_20_sent': False,
        'balance': 0,
        'products': [],
        'pending_payment': None,
        'is_banned': False,
        'is_admin': False,
        'total_spent': 0,
        'total_orders': 0
    }
    for key, value in defaults.items():
        if key not in user_data:
            user_data[key] = value
    if 'join_date' not in user_data:
        user_data['join_date'] = str(datetime.now())
    return user_data

def get_user(user_id, username=None, first_name=None, referrer=None):
    users = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name
        }
        users[user_id_str] = ensure_user_fields(users[user_id_str])
        
        if referrer and str(referrer) in users and referrer != user_id:
            users[user_id_str]['referred_by'] = referrer
            ref_user = ensure_user_fields(users[str(referrer)])
            if user_id not in ref_user['referrals']:
                ref_user['referrals'].append(user_id)
                ref_user['referral_count'] = len(ref_user['referrals'])
                
                if ref_user['referral_count'] == 3 and not ref_user['pending_3_reward'] and not ref_user['claimed_3']:
                    ref_user['pending_3_reward'] = True
                    ref_name = ref_user.get('first_name', 'کاربر')
                    try:
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        markup.add(
                            types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_3reward_{referrer}"),
                            types.InlineKeyboardButton("❌ رد", callback_data=f"reject_3reward_{referrer}")
                        )
                        bot.send_message(
                            referrer,
                            f"🎉 تبریک {ref_name} عزیز!\n\nشما ۳ زیرمجموعه تکمیل کردید!\nبا زدن دکمه تایید، ۱۰۰ مگابایت کانفیگ دریافت می‌کنید.",
                            reply_markup=markup
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                
                if ref_user['referral_count'] == 20 and not ref_user['reward_20_sent']:
                    ref_user['reward_20_sent'] = True
                    ref_name = ref_user.get('first_name', 'کاربر')
                    try:
                        request_id = f"ref20_{referrer}_{int(time.time())}"
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        markup.add(
                            types.InlineKeyboardButton("✅ ارسال کانفیگ ۱ گیگ", callback_data=f"sendconfigref20_{referrer}_{request_id}"),
                            types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"rejectconfigref_{referrer}_{request_id}")
                        )
                        bot.send_message(
                            MAIN_ADMIN_ID,
                            f"🏆 کاربر {ref_name} (ID: {referrer}) به ۲۰ زیرمجموعه رسید.\n\n🎁 جایزه: کانفیگ ۱ گیگابایت\n\n👇 یکی از گزینه‌ها را انتخاب کنید:",
                            reply_markup=markup
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                
                users[str(referrer)] = ref_user
        
        save_users(users)
    else:
        updated = False
        users[user_id_str] = ensure_user_fields(users[user_id_str])
        
        if username and users[user_id_str].get('username') != username:
            users[user_id_str]['username'] = username
            updated = True
        if first_name and users[user_id_str].get('first_name') != first_name:
            users[user_id_str]['first_name'] = first_name
            updated = True
        
        if referrer and str(referrer) in users and not users[user_id_str].get('referred_by') and referrer != user_id:
            users[user_id_str]['referred_by'] = referrer
            ref_user = ensure_user_fields(users[str(referrer)])
            if user_id not in ref_user['referrals']:
                ref_user['referrals'].append(user_id)
                ref_user['referral_count'] = len(ref_user['referrals'])
                
                if ref_user['referral_count'] == 3 and not ref_user['pending_3_reward'] and not ref_user['claimed_3']:
                    ref_user['pending_3_reward'] = True
                    ref_name = ref_user.get('first_name', 'کاربر')
                    try:
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        markup.add(
                            types.InlineKeyboardButton("✅ تایید", callback_data=f"confirm_3reward_{referrer}"),
                            types.InlineKeyboardButton("❌ رد", callback_data=f"reject_3reward_{referrer}")
                        )
                        bot.send_message(
                            referrer,
                            f"🎉 تبریک {ref_name} عزیز!\n\nشما ۳ زیرمجموعه تکمیل کردید!\nبا زدن دکمه تایید، ۱۰۰ مگابایت کانفیگ دریافت می‌کنید.",
                            reply_markup=markup
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                
                if ref_user['referral_count'] == 20 and not ref_user['reward_20_sent']:
                    ref_user['reward_20_sent'] = True
                    ref_name = ref_user.get('first_name', 'کاربر')
                    try:
                        request_id = f"ref20_{referrer}_{int(time.time())}"
                        markup = types.InlineKeyboardMarkup(row_width=2)
                        markup.add(
                            types.InlineKeyboardButton("✅ ارسال کانفیگ ۱ گیگ", callback_data=f"sendconfigref20_{referrer}_{request_id}"),
                            types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"rejectconfigref_{referrer}_{request_id}")
                        )
                        bot.send_message(
                            MAIN_ADMIN_ID,
                            f"🏆 کاربر {ref_name} (ID: {referrer}) به ۲۰ زیرمجموعه رسید.\n\n🎁 جایزه: کانفیگ ۱ گیگابایت\n\n👇 یکی از گزینه‌ها را انتخاب کنید:",
                            reply_markup=markup
                        )
                    except Exception as e:
                        print(f"Error: {e}")
                
                users[str(referrer)] = ref_user
            updated = True
        
        if updated:
            save_users(users)
    
    return users[user_id_str]

def update_user(user_id, data):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)] = ensure_user_fields(users[str(user_id)])
        users[str(user_id)].update(data)
        save_users(users)

def is_admin(user_id):
    admins = load_admins()
    return user_id in admins

def is_user_member(user_id):
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status not in ['left', 'kicked']
    except:
        return False

# ============ کیبوردهای اصلی ============
def main_menu_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🛒 فروشگاه", callback_data="shop")
    btn2 = types.InlineKeyboardButton("📦 کانفیگ‌های من", callback_data="my_products")
    btn3 = types.InlineKeyboardButton("👤 پروفایل", callback_data="profile")
    btn4 = types.InlineKeyboardButton("💰 شارژ کیف پول", callback_data="increase_balance")
    btn5 = types.InlineKeyboardButton("📞 پشتیبانی", callback_data="support")
    btn6 = types.InlineKeyboardButton("👥 رفال", callback_data="referral")
    btn7 = types.InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    return markup

def admin_panel_buttons():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ افزودن محصول", callback_data="admin_add_product"),
        types.InlineKeyboardButton("➖ حذف محصول", callback_data="admin_del_product"),
        types.InlineKeyboardButton("📦 لیست محصولات", callback_data="admin_products_list"),
        types.InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_users_list"),
        types.InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 ارسال همگانی", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("💰 مدیریت موجودی", callback_data="admin_balance"),
        types.InlineKeyboardButton("🚫 بن/آنبن کاربر", callback_data="admin_ban"),
        types.InlineKeyboardButton("👑 مدیریت ادمین‌ها", callback_data="admin_manage_admins"),
        types.InlineKeyboardButton("💾 بکاپ دیتا", callback_data="admin_backup"),
        types.InlineKeyboardButton("🔄 ریست دیتا", callback_data="admin_reset"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")
    )
    return markup

def back_button():
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")
    markup.add(back_btn)
    return markup

def back_to_admin_button():
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("🔙 برگشت به پنل ادمین", callback_data="admin_panel")
    markup.add(back_btn)
    return markup

def confirm_delete_buttons(product_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    confirm = types.InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"delete_yes_{product_id}")
    cancel = types.InlineKeyboardButton("❌ خیر، منصرف شدم", callback_data="delete_no")
    markup.add(confirm, cancel)
    return markup

# ============ راه‌اندازی ربات ============
bot = telebot.TeleBot(TOKEN)
user_states = {}

# ============ دستورات ادمین ============
@bot.message_handler(commands=['admin'])
def admin_panel_command(message):
    if not is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "⛔ شما دسترسی ادمین ندارید!")
        return
    
    bot.send_message(
        message.chat.id,
        "⚙️ **پنل مدیریت ربات**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=admin_panel_buttons(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    if not is_admin(message.from_user.id):
        return
    
    user_states[message.from_user.id] = {'state': 'waiting_broadcast'}
    bot.send_message(
        message.chat.id,
        "📢 **ارسال پیام همگانی**\n\nپیام خود را ارسال کنید.\n(متن، عکس، فایل یا ویدیو)\n\nبرای لغو /cancel را بفرستید.",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['stats'])
def stats_command(message):
    if not is_admin(message.from_user.id):
        return
    
    users = load_users()
    products = load_products()
    
    total_users = len(users)
    banned_users = sum(1 for u in users.values() if u.get('is_banned', False))
    active_users = total_users - banned_users
    
    total_balance = sum(u.get('balance', 0) for u in users.values())
    total_orders = sum(u.get('total_orders', 0) for u in users.values())
    
    stats_text = f"""
📊 **آمار ربات**

👥 کل کاربران: {total_users}
✅ کاربران فعال: {active_users}
🚫 کاربران بن‌شده: {banned_users}
📦 تعداد محصولات: {len(products)}
💰 کل موجودی کاربران: {total_balance:,} تومان
🛒 کل سفارشات: {total_orders}
📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    bot.send_message(message.chat.id, stats_text, parse_mode='Markdown')

# ============ کال‌بک‌های پنل ادمین ============
@bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
def admin_panel_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "⚙️ **پنل مدیریت ربات**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=admin_panel_buttons(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_product")
def admin_add_product(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "➕ **افزودن محصول جدید**\n\nلطفاً **نام محصول** را وارد کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )
    user_states[call.from_user.id] = {'state': 'adding_product_name'}

@bot.callback_query_handler(func=lambda call: call.data == "admin_del_product")
def admin_del_product(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    products = load_products()
    if not products:
        bot.answer_callback_query(call.id, "❌ هیچ محصولی وجود ندارد!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for pid, product in products.items():
        markup.add(types.InlineKeyboardButton(
            f"🗑 {product['name']} - {product['price']:,} تومان",
            callback_data=f"delete_confirm_{pid}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="admin_panel"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🗑 **حذف محصول**\n\nمحصول مورد نظر را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_products_list")
def admin_products_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    products = load_products()
    if not products:
        text = "❌ **هیچ محصولی موجود نیست.**"
    else:
        text = "📦 **لیست محصولات:**\n\n"
        for pid, product in products.items():
            text += f"🆔 {pid}\n📌 {product['name']}\n💰 {product['price']:,} تومان\n━━━━━━━━━━━━━━━\n"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_users_list")
def admin_users_list(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    users = load_users()
    if not users:
        text = "❌ **هیچ کاربری یافت نشد.**"
    else:
        # نمایش ۱۰ کاربر اول
        text = "👥 **لیست کاربران (۱۰ نفر اول):**\n\n"
        count = 0
        for uid, user in users.items():
            if count >= 10:
                break
            text += f"🆔 {uid}\n👤 {user.get('first_name', 'نامشخص')}\n💰 {user.get('balance', 0):,} تومان\n📦 {len(user.get('products', []))} خرید\n━━━━━━━━━━━━━━━\n"
            count += 1
        text += f"\n📊 **کل کاربران:** {len(users)} نفر"
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    users = load_users()
    products = load_products()
    
    total_users = len(users)
    banned_users = sum(1 for u in users.values() if u.get('is_banned', False))
    active_users = total_users - banned_users
    total_balance = sum(u.get('balance', 0) for u in users.values())
    total_orders = sum(u.get('total_orders', 0) for u in users.values())
    
    stats_text = f"""
📊 **آمار ربات**

👥 کل کاربران: {total_users}
✅ کاربران فعال: {active_users}
🚫 کاربران بن‌شده: {banned_users}
📦 تعداد محصولات: {len(products)}
💰 کل موجودی کاربران: {total_balance:,} تومان
🛒 کل سفارشات: {total_orders}
📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        stats_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "📢 **ارسال پیام همگانی**\n\nلطفاً پیام خود را ارسال کنید.\n(متن، عکس، فایل یا ویدیو)\n\n⚠️ پیام به **همه کاربران** ارسال خواهد شد.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )
    user_states[call.from_user.id] = {'state': 'waiting_broadcast'}

@bot.callback_query_handler(func=lambda call: call.data == "admin_balance")
def admin_balance_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "💰 **مدیریت موجودی کاربران**\n\nلطفاً **آیدی کاربر** را وارد کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )
    user_states[call.from_user.id] = {'state': 'waiting_balance_user_id'}

@bot.callback_query_handler(func=lambda call: call.data == "admin_ban")
def admin_ban_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🚫 **بن/آنبن کاربر**\n\nلطفاً **آیدی کاربر** را وارد کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )
    user_states[call.from_user.id] = {'state': 'waiting_ban_user_id'}

@bot.callback_query_handler(func=lambda call: call.data == "admin_manage_admins")
def admin_manage_admins(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    admins = load_admins()
    text = "👑 **مدیریت ادمین‌ها**\n\n"
    text += f"👤 ادمین اصلی: {MAIN_ADMIN_ID}\n\n"
    text += "📋 **لیست ادمین‌ها:**\n"
    for admin in admins:
        text += f"• {admin}\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ افزودن ادمین", callback_data="admin_add_admin"),
        types.InlineKeyboardButton("➖ حذف ادمین", callback_data="admin_remove_admin"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="admin_panel")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "admin_add_admin")
def admin_add_admin(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "➕ **افزودن ادمین جدید**\n\nلطفاً **آیدی عددی** ادمین جدید را وارد کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )
    user_states[call.from_user.id] = {'state': 'waiting_add_admin'}

@bot.callback_query_handler(func=lambda call: call.data == "admin_remove_admin")
def admin_remove_admin(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    admins = load_admins()
    if len(admins) <= 1:
        bot.answer_callback_query(call.id, "❌ حداقل یک ادمین باید وجود داشته باشد!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for admin in admins:
        if admin != MAIN_ADMIN_ID:
            markup.add(types.InlineKeyboardButton(
                f"🗑 حذف ادمین {admin}",
                callback_data=f"remove_admin_{admin}"
            ))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="admin_manage_admins"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "👑 **حذف ادمین**\n\nادمین مورد نظر را انتخاب کنید:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_admin_"))
def remove_admin_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    admin_id = int(call.data.split("_")[2])
    admins = load_admins()
    
    if admin_id in admins:
        admins.remove(admin_id)
        save_admins(admins)
        bot.answer_callback_query(call.id, f"✅ ادمین {admin_id} حذف شد!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ ادمین یافت نشد!", show_alert=True)
    
    # برگشت به منوی مدیریت ادمین‌ها
    admin_manage_admins(call)

@bot.callback_query_handler(func=lambda call: call.data == "admin_backup")
def admin_backup(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    # ایجاد فایل بکاپ
    backup_data = {
        'users': load_users(),
        'products': load_products(),
        'admins': load_admins(),
        'settings': load_settings(),
        'backup_date': str(datetime.now())
    }
    
    filename = f"backup_{int(time.time())}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=4)
    
    bot.answer_callback_query(call.id, "✅ بکاپ ایجاد شد!", show_alert=True)
    
    # ارسال فایل بکاپ
    with open(filepath, 'rb') as f:
        bot.send_document(
            call.message.chat.id,
            f,
            caption=f"💾 **بکاپ دیتا**\n📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            reply_markup=back_to_admin_button()
        )
    
    # پاک کردن فایل بعد از ارسال
    os.remove(filepath)

@bot.callback_query_handler(func=lambda call: call.data == "admin_reset")
def admin_reset(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚠️ بله، ریست کن", callback_data="reset_confirm"),
        types.InlineKeyboardButton("❌ لغو", callback_data="admin_panel")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "⚠️ **هشدار!**\n\nآیا از ریست کردن تمام دیتا مطمئن هستید؟\n\nاین کار **غیرقابل بازگشت** است!",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "reset_confirm")
def reset_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    # پاک کردن دیتا
    save_users({})
    save_products({})
    save_admins([MAIN_ADMIN_ID])
    save_settings({})
    save_broadcast_log([])
    
    bot.answer_callback_query(call.id, "✅ تمام دیتا با موفقیت ریست شد!", show_alert=True)
    bot.edit_message_text(
        "✅ **دیتا با موفقیت ریست شد.**\n\nهمه چیز به حالت اولیه برگشت.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_to_admin_button()
    )

# ============ هندلرهای پیام برای حالت‌های مختلف ============
@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_broadcast')
def handle_broadcast(message):
    if not is_admin(message.from_user.id):
        return
    
    if message.text == '/cancel':
        del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ ارسال همگانی لغو شد.", reply_markup=back_to_admin_button())
        return
    
    users = load_users()
    success = 0
    fail = 0
    
    status_msg = bot.send_message(message.chat.id, "⏳ در حال ارسال پیام همگانی...")
    
    for user_id in users.keys():
        try:
            if message.text:
                bot.send_message(int(user_id), message.text)
            elif message.photo:
                bot.send_photo(int(user_id), message.photo[-1].file_id, caption=message.caption)
            elif message.document:
                bot.send_document(int(user_id), message.document.file_id, caption=message.caption)
            elif message.video:
                bot.send_video(int(user_id), message.video.file_id, caption=message.caption)
            else:
                continue
            success += 1
            time.sleep(0.1)  # جلوگیری از محدودیت
        except:
            fail += 1
    
    # ذخیره لاگ
    log = load_broadcast_log()
    log.append({
        'admin': message.from_user.id,
        'date': str(datetime.now()),
        'success': success,
        'fail': fail,
        'message_type': 'text' if message.text else 'media'
    })
    save_broadcast_log(log)
    
    bot.edit_message_text(
        f"✅ **ارسال همگانی کامل شد!**\n\n✅ موفق: {success}\n❌ ناموفق: {fail}\n👥 کل کاربران: {len(users)}",
        message.chat.id,
        status_msg.message_id,
        reply_markup=back_to_admin_button(),
        parse_mode='Markdown'
    )
    
    del user_states[message.from_user.id]

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_balance_user_id')
def handle_balance_user_id(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
        user_data = get_user(user_id)
        current_balance = user_data.get('balance', 0)
        
        user_states[message.from_user.id] = {
            'state': 'waiting_balance_amount',
            'target_user': user_id
        }
        
        bot.send_message(
            message.chat.id,
            f"💰 **مدیریت موجودی کاربر {user_id}**\n\nموجودی فعلی: {current_balance:,} تومان\n\nلطفاً مبلغ جدید را وارد کنید (عدد مثبت یا منفی):",
            reply_markup=back_to_admin_button()
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک آیدی عددی معتبر وارد کنید!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_balance_amount')
def handle_balance_amount(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        amount = int(message.text.strip())
        target_user = user_states[message.from_user.id]['target_user']
        
        user_data = get_user(target_user)
        new_balance = user_data.get('balance', 0) + amount
        
        if new_balance < 0:
            new_balance = 0
        
        update_user(target_user, {'balance': new_balance})
        
        bot.send_message(
            message.chat.id,
            f"✅ **موجودی کاربر {target_user} به‌روز شد!**\n\n💰 موجودی جدید: {new_balance:,} تومان",
            reply_markup=back_to_admin_button()
        )
        
        # اطلاع‌رسانی به کاربر
        try:
            if amount > 0:
                bot.send_message(
                    target_user,
                    f"💰 **کیف پول شما شارژ شد!**\n\nمبلغ: +{amount:,} تومان\nموجودی جدید: {new_balance:,} تومان"
                )
            elif amount < 0:
                bot.send_message(
                    target_user,
                    f"💰 **مبلغی از کیف پول شما کسر شد!**\n\nمبلغ: {amount:,} تومان\nموجودی جدید: {new_balance:,} تومان"
                )
        except:
            pass
        
        del user_states[message.from_user.id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_ban_user_id')
def handle_ban_user_id(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
        user_data = get_user(user_id)
        is_banned = user_data.get('is_banned', False)
        
        new_status = not is_banned
        update_user(user_id, {'is_banned': new_status})
        
        status_text = "بن" if new_status else "آنبن"
        bot.send_message(
            message.chat.id,
            f"✅ **کاربر {user_id} با موفقیت {status_text} شد!**",
            reply_markup=back_to_admin_button()
        )
        
        # اطلاع‌رسانی به کاربر
        try:
            if new_status:
                bot.send_message(
                    user_id,
                    "🚫 **شما توسط ادمین بن شدید!**\n\nبرای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
                )
            else:
                bot.send_message(
                    user_id,
                    "✅ **بن شما لغو شد!**\n\nمی‌توانید مجدداً از ربات استفاده کنید."
                )
        except:
            pass
        
        del user_states[message.from_user.id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک آیدی عددی معتبر وارد کنید!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_add_admin')
def handle_add_admin(message):
    if not is_admin(message.from_user.id):
        return
    
    try:
        user_id = int(message.text.strip())
        admins = load_admins()
        
        if user_id in admins:
            bot.send_message(message.chat.id, "❌ این کاربر قبلاً ادمین است!")
            return
        
        admins.append(user_id)
        save_admins(admins)
        
        bot.send_message(
            message.chat.id,
            f"✅ **ادمین {user_id} با موفقیت اضافه شد!**",
            reply_markup=back_to_admin_button()
        )
        
        try:
            bot.send_message(
                user_id,
                "👑 **تبریک! شما به عنوان ادمین ربات اضافه شدید!**\n\nاز دستور /admin برای دسترسی به پنل مدیریت استفاده کنید."
            )
        except:
            pass
        
        del user_states[message.from_user.id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک آیدی عددی معتبر وارد کنید!")

# ============ بقیه کال‌بک‌ها ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_confirm_"))
def delete_product_confirm(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    product_id = call.data.split("_")[2]
    products = load_products()
    product = products.get(product_id)
    
    if not product:
        bot.answer_callback_query(call.id, "❌ محصول یافت نشد!", show_alert=True)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"delete_yes_{product_id}"),
        types.InlineKeyboardButton("❌ لغو", callback_data="admin_del_product")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"⚠️ **تأیید حذف**\n\nآیا از حذف محصول زیر مطمئن هستید؟\n\n📌 {product['name']}\n💰 {product['price']:,} تومان",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_yes_"))
def delete_product_yes(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    product_id = call.data.split("_")[2]
    products = load_products()
    
    if product_id in products:
        del products[product_id]
        save_products(products)
        bot.answer_callback_query(call.id, "✅ محصول با موفقیت حذف شد!", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ محصول یافت نشد!", show_alert=True)
    
    admin_panel_callback(call)

@bot.callback_query_handler(func=lambda call: call.data == "delete_no")
def delete_no(call):
    bot.answer_callback_query(call.id, "❌ عملیات لغو شد!")
    admin_del_product(call)

# ============ بقیه کدهای ربات ============
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    referrer = None
    args = message.text.split()
    if len(args) > 1 and args[1].startswith('ref'):
        try:
            referrer = int(args[1][3:])
        except:
            pass
    
    user_data = get_user(user_id, username, first_name, referrer)
    
    # بررسی بن بودن
    if user_data.get('is_banned', False):
        bot.send_message(chat_id, "🚫 **شما توسط ادمین بن شده‌اید!**\n\nبرای اطلاعات بیشتر با پشتیبانی تماس بگیرید.")
        return
    
    if is_user_member(user_id):
        welcome_text = f"""سلام {first_name} عزیز! 👋

به ربات فروش کانفیگ خوش آمدید.

برای استفاده از خدمات، لطفاً از منوی زیر اقدام کنید."""
        
        markup = main_menu_buttons()
        # نمایش دکمه ادمین فقط برای ادمین‌ها
        if is_admin(user_id):
            pass  # دکمه ادمین قبلاً در main_menu_buttons اضافه شده
        
        bot.send_message(chat_id, welcome_text, reply_markup=markup)
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        join_button = types.InlineKeyboardButton("🔗 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        check_button = types.InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_sub")
        keyboard.add(join_button, check_button)
        bot.send_message(
            chat_id,
            f"برای استفاده از ربات، ابتدا در کانال زیر عضو شوید:\n{CHANNEL_USERNAME}",
            reply_markup=keyboard
        )

# ============ محصولات (بقیه کدها) ============
@bot.message_handler(commands=['addproduct'])
def add_product_start(message):
    if not is_admin(message.from_user.id):
        return
    user_states[message.from_user.id] = {'state': 'adding_product_name'}
    bot.send_message(message.chat.id, "➕ لطفاً نام محصول را وارد کنید:")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'adding_product_name' and is_admin(message.from_user.id))
def get_product_name(message):
    product_name = message.text.strip()
    user_states[message.from_user.id]['product_name'] = product_name
    user_states[message.from_user.id]['state'] = 'adding_product_price'
    bot.send_message(message.chat.id, "💰 لطفاً قیمت محصول را به تومان وارد کنید:")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'adding_product_price' and is_admin(message.from_user.id))
def get_product_price(message):
    try:
        price = int(message.text.strip())
        if price <= 0:
            bot.send_message(message.chat.id, "❌ لطفاً یک عدد مثبت وارد کنید.")
            return
        
        product_name = user_states[message.from_user.id]['product_name']
        products = load_products()
        new_id = str(len(products) + 1)
        products[new_id] = {'name': product_name, 'price': price}
        save_products(products)
        
        bot.send_message(
            message.chat.id,
            f"✅ **محصول با موفقیت اضافه شد!**\n\n📌 نام: {product_name}\n💰 قیمت: {price:,} تومان",
            reply_markup=back_to_admin_button()
        )
        del user_states[message.from_user.id]
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید.")

# ============ کال‌بک‌های اصلی کاربر ============
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    first_name = call.from_user.first_name
    
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    if is_user_member(user_id):
        bot.edit_message_text("✅ عضویت شما تأیید شد.", chat_id, message_id)
        bot.send_message(chat_id, welcome_message_for_member(first_name), reply_markup=main_menu_buttons())
    else:
        bot.answer_callback_query(call.id, "❌ هنوز عضو نشده‌اید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_main_menu(call):
    chat_id = call.message.chat.id
    first_name = call.from_user.first_name
    bot.answer_callback_query(call.id)
    
    user_data = get_user(call.from_user.id)
    if user_data.get('is_banned', False):
        bot.edit_message_text("🚫 شما بن هستید!", chat_id, call.message.message_id)
        return
    
    bot.edit_message_text(
        welcome_message_for_member(first_name),
        chat_id,
        call.message.message_id,
        reply_markup=main_menu_buttons()
    )

@bot.callback_query_handler(func=lambda call: call.data == "shop")
def show_shop(call):
    chat_id = call.message.chat.id
    user_data = get_user(call.from_user.id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    products = load_products()
    if not products:
        bot.answer_callback_query(call.id)
        bot.edit_message_text("❌ در حال حاضر محصولی موجود نیست.", chat_id, call.message.message_id, reply_markup=back_button())
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for product_id, product in products.items():
        markup.add(types.InlineKeyboardButton(
            f"{product['name']} - {product['price']:,} تومان",
            callback_data=f"buy_product_{product_id}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🛒 **فروشگاه کانفیگ**\n\nلطفاً محصول مورد نظر خود را انتخاب کنید:",
        chat_id,
        call.message.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_product_"))
def buy_product(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    product_id = call.data.split("_")[2]
    products = load_products()
    product = products.get(product_id)
    
    if not product:
        bot.answer_callback_query(call.id, "❌ محصول مورد نظر یافت نشد.", show_alert=True)
        return
    
    balance = user_data.get('balance', 0)
    
    if balance >= product['price']:
        new_balance = balance - product['price']
        update_user(user_id, {'balance': new_balance})
        
        products_list = user_data.get('products', [])
        products_list.append(f"{product['name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        update_user(user_id, {
            'products': products_list,
            'total_spent': user_data.get('total_spent', 0) + product['price'],
            'total_orders': user_data.get('total_orders', 0) + 1
        })
        
        request_id = f"{user_id}_{int(time.time())}"
        
        bot.answer_callback_query(call.id, "✅ خرید با موفقیت ثبت شد!", show_alert=True)
        bot.edit_message_text(
            f"✅ **خرید شما ثبت شد!**\n\n📦 محصول: {product['name']}\n💰 مبلغ: {product['price']:,} تومان\n💵 موجودی جدید: {new_balance:,} تومان\n\n⏳ منتظر ارسال کانفیگ از طرف ادمین باشید...",
            chat_id,
            call.message.message_id,
            reply_markup=back_button()
        )
        
        admin_text = (
            f"🔔 **درخواست کانفیگ جدید**\n\n"
            f"👤 نام: {call.from_user.first_name}\n"
            f"🆔 آیدی: {user_id}\n"
            f"📛 یوزرنیم: @{call.from_user.username or 'ندارد'}\n"
            f"📦 محصول: {product['name']}\n"
            f"💰 قیمت: {product['price']:,} تومان\n"
            f"💵 موجودی پس از خرید: {new_balance:,} تومان"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"sendconfig_{user_id}_{request_id}"),
            types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"rejectconfig_{user_id}_{request_id}")
        )
        
        bot.send_message(MAIN_ADMIN_ID, admin_text, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, f"❌ موجودی کافی نیست!\nموجودی: {balance:,} تومان", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendconfig_"))
def ask_for_config_link(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    request_id = parts[2]
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"✍️ **ارسال کانفیگ به کاربر {user_id}**\n\nلطفاً لینک کانفیگ را ارسال کنید.\n(متن، عکس یا فایل)\n\n⚠️ روی پیام **ریپلای** کنید و سپس ارسال کنید.",
        call.message.chat.id,
        call.message.message_id
    )
    
    user_states[call.from_user.id] = {
        'state': 'waiting_config_reply',
        'target_user': user_id,
        'request_id': request_id,
        'msg_id': call.message.message_id,
        'chat_id': call.message.chat.id
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("rejectconfig_"))
def reject_config_request(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    
    bot.answer_callback_query(call.id, "❌ درخواست رد شد!", show_alert=True)
    bot.edit_message_text(
        f"❌ درخواست کاربر {user_id} رد شد.",
        call.message.chat.id,
        call.message.message_id
    )
    
    try:
        bot.send_message(user_id, "❌ درخواست خرید شما رد شد.\n\nلطفاً با پشتیبانی تماس بگیرید.")
    except:
        pass

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_config_reply' and is_admin(message.from_user.id))
def send_config_to_user(message):
    target_user = user_states[message.from_user.id]['target_user']
    msg_id = user_states[message.from_user.id]['msg_id']
    chat_id = user_states[message.from_user.id]['chat_id']
    
    try:
        if message.text:
            bot.send_message(target_user, f"🔐 **کانفیگ شما:**\n\n{message.text}")
        elif message.document:
            bot.send_document(target_user, message.document.file_id, caption="🔐 فایل کانفیگ شما")
        elif message.photo:
            bot.send_photo(target_user, message.photo[-1].file_id, caption="🔐 تصویر کانفیگ شما")
        else:
            bot.send_message(message.chat.id, "❌ نوع فایل پشتیبانی نمی‌شود!")
            return
        
        bot.edit_message_text(
            f"✅ کانفیگ با موفقیت به کاربر {target_user} ارسال شد.",
            chat_id,
            msg_id
        )
        
        bot.send_message(message.chat.id, f"✅ **کانفیگ به کاربر {target_user} ارسال شد!**")
        del user_states[message.from_user.id]
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال: {str(e)}")

# ============ سایر کال‌بک‌های کاربر ============
@bot.callback_query_handler(func=lambda call: call.data == "my_products")
def show_my_products(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    products = user_data.get('products', [])
    
    if products:
        products_text = "\n".join([f"• {p}" for p in products])
        text = f"📦 **کانفیگ‌های خریداری شده**\n\n{products_text}"
    else:
        text = "❌ شما تاکنون کانفیگی خریداری نکرده‌اید."
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=back_button(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def show_profile(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    balance = user_data.get('balance', 0)
    join_date = user_data.get('join_date', 'نامشخص')
    products_count = len(user_data.get('products', []))
    ref_count = user_data.get('referral_count', 0)
    total_spent = user_data.get('total_spent', 0)
    
    text = f"""👤 **پروفایل کاربری**

👤 نام: {call.from_user.first_name}
🆔 آیدی: {user_id}
📛 یوزرنیم: @{call.from_user.username or 'ندارد'}
💰 موجودی: {balance:,} تومان
💸 کل خرید: {total_spent:,} تومان
📦 تعداد خرید: {products_count} عدد
👥 زیرمجموعه: {ref_count} نفر
📅 عضویت: {join_date.split()[0] if ' ' in join_date else join_date}
✅ وضعیت: {'فعال' if not user_data.get('is_banned') else 'بن شده'}"""
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=back_button(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "increase_balance")
def increase_balance(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"💰 **شارژ کیف پول**\n\n💳 **اطلاعات کارت:**\nکارت: 6037-****-****-1234\nبه نام: شرکت نمونه\n\n📸 پس از واریز، **تصویر فیش** را ارسال کنید.\n\nحداقل شارژ: 10,000 تومان",
        chat_id,
        call.message.message_id,
        reply_markup=back_button()
    )
    user_states[user_id] = {'state': 'waiting_payment_image'}

@bot.message_handler(content_types=['photo'])
def handle_payment_image(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_states.get(user_id, {}).get('state') == 'waiting_payment_image':
        username = message.from_user.username or 'ندارد'
        first_name = message.from_user.first_name
        photo_id = message.photo[-1].file_id
        payment_id = str(int(time.time()))
        
        update_user(user_id, {'pending_payment': payment_id})
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ تایید پرداخت", callback_data=f"confirmpay_{user_id}_{payment_id}"),
            types.InlineKeyboardButton("❌ رد پرداخت", callback_data=f"rejectpay_{user_id}_{payment_id}")
        )
        
        bot.send_message(
            MAIN_ADMIN_ID,
            f"💳 **درخواست شارژ کیف پول**\n\n👤 نام: {first_name}\n🆔 آیدی: {user_id}\n📛 یوزرنیم: @{username}\n🔢 کد: {payment_id}",
            reply_markup=markup
        )
        bot.send_photo(MAIN_ADMIN_ID, photo_id, caption=f"فیش واریز از {first_name}")
        
        bot.send_message(
            chat_id,
            "✅ **فیش واریز دریافت شد!**\n\nدرخواست شما به ادمین ارسال شد.\nپس از تأیید، موجودی شما افزایش می‌یابد.",
            reply_markup=back_button()
        )
        
        del user_states[user_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirmpay_"))
def confirm_payment(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data_parts = call.data.split("_")
    user_id = int(data_parts[1])
    payment_id = data_parts[2]
    
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"💰 لطفاً **مبلغ واریزی** کاربر {user_id} را به تومان وارد کنید:"
    )
    user_states[call.from_user.id] = {
        'state': 'waiting_payment_amount',
        'target_user': user_id,
        'payment_id': payment_id,
        'msg_id': call.message.message_id,
        'chat_id': call.message.chat.id
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("rejectpay_"))
def reject_payment(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    data_parts = call.data.split("_")
    user_id = int(data_parts[1])
    
    bot.answer_callback_query(call.id, "❌ پرداخت رد شد!", show_alert=True)
    
    update_user(user_id, {'pending_payment': None})
    
    try:
        bot.send_message(user_id, "❌ پرداخت شما رد شد.\n\nلطفاً مجدداً اقدام کنید.")
    except:
        pass
    
    bot.edit_message_text(
        f"❌ پرداخت کاربر {user_id} رد شد.",
        call.message.chat.id,
        call.message.message_id
    )

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_payment_amount' and is_admin(message.from_user.id))
def handle_payment_amount(message):
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ لطفاً یک عدد مثبت وارد کنید!")
            return
        
        target_user = user_states[message.from_user.id]['target_user']
        payment_id = user_states[message.from_user.id]['payment_id']
        
        user_data = get_user(target_user)
        new_balance = user_data.get('balance', 0) + amount
        update_user(target_user, {'balance': new_balance, 'pending_payment': None})
        
        bot.send_message(
            message.chat.id,
            f"✅ **موجودی کاربر {target_user} افزایش یافت!**\n\n💰 مبلغ: {amount:,} تومان\n💵 موجودی جدید: {new_balance:,} تومان",
            reply_markup=back_to_admin_button()
        )
        
        try:
            bot.send_message(
                target_user,
                f"✅ **کیف پول شما شارژ شد!**\n\n💰 مبلغ: {amount:,} تومان\n💵 موجودی جدید: {new_balance:,} تومان"
            )
        except:
            pass
        
        del user_states[message.from_user.id]
        
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید!")

@bot.callback_query_handler(func=lambda call: call.data == "support")
def show_support(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"📞 **پشتیبانی**\n\n🆔 آیدی پشتیبان: `{MAIN_ADMIN_ID}`\n\nبرای ارتباط با پشتیبان، به آیدی بالا پیام دهید.",
        chat_id,
        call.message.message_id,
        reply_markup=back_button(),
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == "referral")
def show_referral(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    user_data = get_user(user_id)
    if user_data.get('is_banned', False):
        bot.answer_callback_query(call.id, "🚫 شما بن هستید!", show_alert=True)
        return
    
    ref_count = user_data.get('referral_count', 0)
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start=ref{user_id}"
    
    text = f"""👥 **سیستم زیرمجموعه‌گیری**

🔗 **لینک دعوت شما:**
`{ref_link}`

👥 تعداد زیرمجموعه: {ref_count} نفر

🎁 **جوایز:**
• ۳ زیرمجموعه: ۱۰۰ مگابایت کانفیگ
• ۲۰ زیرمجموعه: ۱ گیگابایت کانفیگ

📌 لینک رو برای دوستانت بفرست تا زیرمجموعه تو بشن."""
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔗 ارسال لینک", url=f"https://t.me/share/url?url={ref_link}"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_menu")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')

# ============ کال‌بک‌های جایزه رفال ============
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_3reward_"))
def confirm_3reward(call):
    user_id = int(call.data.split("_")[2])
    users = load_users()
    user_str = str(user_id)
    
    if user_str in users:
        users[user_str] = ensure_user_fields(users[user_str])
        if users[user_str].get('pending_3_reward'):
            users[user_str]['pending_3_reward'] = False
            users[user_str]['claimed_3'] = True
            save_users(users)
            
            request_id = f"ref3_{user_id}_{int(time.time())}"
            
            bot.answer_callback_query(call.id, "✅ درخواست شما به ادمین ارسال شد!", show_alert=True)
            bot.edit_message_text(
                "✅ **درخواست کانفیگ ۱۰۰ مگابایتی ثبت شد!**\n\nمنتظر ارسال از طرف ادمین باشید.",
                call.message.chat.id,
                call.message.message_id
            )
            
            admin_text = (
                f"🎁 **درخواست کانفیگ رفال (۳ زیرمجموعه)**\n\n"
                f"👤 نام: {users[user_str].get('first_name', 'کاربر')}\n"
                f"🆔 آیدی: {user_id}\n"
                f"📛 یوزرنیم: @{users[user_str].get('username', 'ندارد')}\n"
                f"🎁 جایزه: کانفیگ ۱۰۰ مگابایت"
            )
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("✅ ارسال کانفیگ ۱۰۰ مگ", callback_data=f"sendconfigref3_{user_id}_{request_id}"),
                types.InlineKeyboardButton("❌ رد درخواست", callback_data=f"rejectconfigref_{user_id}_{request_id}")
            )
            
            bot.send_message(MAIN_ADMIN_ID, admin_text, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "❌ درخواست معتبر نیست!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_3reward_"))
def reject_3reward(call):
    user_id = int(call.data.split("_")[2])
    users = load_users()
    user_str = str(user_id)
    
    if user_str in users:
        users[user_str] = ensure_user_fields(users[user_str])
        if users[user_str].get('pending_3_reward'):
            users[user_str]['pending_3_reward'] = False
            save_users(users)
            
            bot.answer_callback_query(call.id, "❌ جایزه ۱۰۰ مگابایتی رد شد!", show_alert=True)
            bot.edit_message_text(
                "❌ شما جایزه ۱۰۰ مگابایتی را رد کردید.\n\nبا ۲۰ زیرمجموعه، ادمین برات ۱ گیگابایت ارسال می‌کنه.",
                call.message.chat.id,
                call.message.message_id
            )
    else:
        bot.answer_callback_query(call.id, "❌ درخواست معتبر نیست!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendconfigref3_"))
def send_ref3_config(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    request_id = parts[2]
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"✍️ **ارسال کانفیگ ۱۰۰ مگابایت به کاربر {user_id}**\n\nلطفاً لینک کانفیگ را ارسال کنید.\n(متن، عکس یا فایل)",
        call.message.chat.id,
        call.message.message_id
    )
    
    user_states[call.from_user.id] = {
        'state': 'waiting_ref_config',
        'target_user': user_id,
        'request_id': request_id,
        'msg_id': call.message.message_id,
        'chat_id': call.message.chat.id,
        'type': 'ref3'
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("sendconfigref20_"))
def send_ref20_config(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    request_id = parts[2]
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"✍️ **ارسال کانفیگ ۱ گیگابایت به کاربر {user_id}**\n\nلطفاً لینک کانفیگ را ارسال کنید.\n(متن، عکس یا فایل)",
        call.message.chat.id,
        call.message.message_id
    )
    
    user_states[call.from_user.id] = {
        'state': 'waiting_ref_config',
        'target_user': user_id,
        'request_id': request_id,
        'msg_id': call.message.message_id,
        'chat_id': call.message.chat.id,
        'type': 'ref20'
    }

@bot.callback_query_handler(func=lambda call: call.data.startswith("rejectconfigref_"))
def reject_ref_config(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "⛔ دسترسی غیرمجاز!", show_alert=True)
        return
    
    parts = call.data.split("_")
    user_id = int(parts[1])
    request_id = parts[2]
    
    bot.answer_callback_query(call.id, "❌ درخواست رد شد!", show_alert=True)
    bot.edit_message_text(
        f"❌ درخواست رفال کاربر {user_id} رد شد.",
        call.message.chat.id,
        call.message.message_id
    )
    
    try:
        bot.send_message(user_id, "❌ متأسفانه درخواست جایزه رفال شما رد شد.\n\nلطفاً با پشتیبانی تماس بگیرید.")
    except:
        pass

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, {}).get('state') == 'waiting_ref_config' and is_admin(message.from_user.id))
def send_ref_config(message):
    target_user = user_states[message.from_user.id]['target_user']
    msg_id = user_states[message.from_user.id]['msg_id']
    chat_id = user_states[message.from_user.id]['chat_id']
    ref_type = user_states[message.from_user.id].get('type', 'ref3')
    
    size = "۱۰۰ مگابایت" if ref_type == 'ref3' else "۱ گیگابایت"
    
    try:
        if message.text:
            bot.send_message(target_user, f"🔐 **کانفیگ {size} شما:**\n\n{message.text}")
        elif message.document:
            bot.send_document(target_user, message.document.file_id, caption=f"🔐 کانفیگ {size} شما")
        elif message.photo:
            bot.send_photo(target_user, message.photo[-1].file_id, caption=f"🔐 کانفیگ {size} شما")
        else:
            bot.send_message(message.chat.id, "❌ نوع فایل پشتیبانی نمی‌شود!")
            return
        
        bot.edit_message_text(
            f"✅ کانفیگ {size} با موفقیت به کاربر {target_user} ارسال شد.",
            chat_id,
            msg_id
        )
        
        bot.send_message(message.chat.id, f"✅ **کانفیگ به کاربر {target_user} ارسال شد!**")
        del user_states[message.from_user.id]
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ خطا در ارسال: {str(e)}")

# ============ اجرای ربات ============
def welcome_message_for_member(first_name):
    return f"""سلام {first_name} عزیز! 👋

به ربات فروش کانفیگ خوش آمدید.

برای استفاده از خدمات، لطفاً از منوی زیر اقدام کنید."""

print("✅ ربات با موفقیت روشن شد...")
print(f"👑 ادمین اصلی: {MAIN_ADMIN_ID}")
print(f"📢 کانال: {CHANNEL_USERNAME}")

try:
    bot.infinity_polling()
except Exception as e:
    print(f"❌ خطا: {e}")
