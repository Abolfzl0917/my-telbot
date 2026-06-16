<?php
// ============================================
// ✅ پاسخ به Healthcheck برای Railway
// ============================================
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    http_response_code(200);
    echo "OK";
    exit;
}

// ============================================
// تنظیمات اولیه
// ============================================
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', 'php-error.log');

// ============ تنظیمات اولیه ============
define('API_KEY', getenv('API_KEY') ?: '8262116870:AAESTHjD7Vhph5EGRhBqV_2lHpuQ5tI5LnQ');
define('ADMIN_ID', getenv('ADMIN_ID') ?: 6443963679);

// ============ تابع ارتباط با تلگرام ============
function bot($method, $datas = []) {
    $url = "https://api.telegram.org/bot" . API_KEY . "/" . $method;
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $datas);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    $res = curl_exec($ch);
    if (curl_error($ch)) {
        error_log("CURL Error: " . curl_error($ch));
        return null;
    }
    curl_close($ch);
    return json_decode($res);
}

// ============ دریافت آپدیت ============
$update = json_decode(file_get_contents('php://input'));
if (!isset($update)) {
    exit;
}

// ============ استخراج اطلاعات ============
if (isset($update->message)) {
    $message = $update->message;
    $chat_id = $message->chat->id;
    $text = isset($message->text) ? $message->text : '';
    $from_id = $message->from->id;
    $message_id = $message->message_id;
    $username = isset($message->from->username) ? $message->from->username : '';
    $first_name = isset($message->from->first_name) ? $message->from->first_name : '';
} elseif (isset($update->callback_query)) {
    $callback_query = $update->callback_query;
    $chat_id = $callback_query->message->chat->id;
    $data = $callback_query->data;
    $from_id = $callback_query->from->id;
    $message_id = $callback_query->message->message_id;
    $username = isset($callback_query->from->username) ? $callback_query->from->username : '';
    $first_name = isset($callback_query->from->first_name) ? $callback_query->from->first_name : '';
} else {
    exit;
}

// ============ مدیریت دیتابیس (JSON) ============
$db_file = 'db.json';
if (!file_exists($db_file)) {
    $init = [
        'users' => [],
        'services' => [],
        'configs' => [],
        'channels' => ['lchiik'],
        'status' => 'on',
        'orders' => [],
        'settings' => [
            'card_number' => '5859471029562323',
            'card_holder' => 'عماد صادقی'
        ]
    ];
    file_put_contents($db_file, json_encode($init, JSON_PRETTY_PRINT));
}

$db = json_decode(file_get_contents($db_file), true);
if ($db === null) {
    $db = [
        'users' => [],
        'services' => [],
        'configs' => [],
        'channels' => ['lchiik'],
        'status' => 'on',
        'orders' => [],
        'settings' => [
            'card_number' => '5859471029562323',
            'card_holder' => 'عماد صادقی'
        ]
    ];
    file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
}

// ============ ثبت کاربر جدید ============
if (!isset($db['users'][$from_id])) {
    $db['users'][$from_id] = [
        'step' => 'none',
        'wallet' => 0,
        'my_services' => [],
        'username' => $username,
        'first_name' => $first_name,
        'joined_at' => date('Y-m-d H:i:s')
    ];
    file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
}

// ============ بررسی وضعیت ربات ============
if ($db['status'] == 'off' && $from_id != ADMIN_ID) {
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "⚠️ ربات موقتا در دست تعمیر است. لطفا بعدا مراجعه کنید."
    ]);
    exit;
}

// ============ تابع بررسی عضویت ============
function checkJoin($user_id) {
    global $db;
    if (empty($db['channels'])) {
        return true;
    }
    foreach ($db['channels'] as $ch) {
        $check = bot('getChatMember', ['chat_id' => "@" . $ch, 'user_id' => $user_id]);
        if ($check && isset($check->result)) {
            $status = $check->result->status;
            if ($status == 'left' || $status == 'kicked') {
                return false;
            }
        } else {
            return false;
        }
    }
    return true;
}

// ============ کیبورد اصلی ============
$main_keyboard = json_encode([
    'keyboard' => [
        [['text' => "🛍️ خرید سرویس"]],
        [['text' => "💳 کیف پول"], ['text' => "📦 سرویس‌های من"]],
        [['text' => "☎️ تماس با پشتیبانی"]]
    ],
    'resize_keyboard' => true
]);

// ============ بررسی عضویت در کانال‌ها ============
if (isset($text) && !checkJoin($from_id) && $text != '/start') {
    $db['users'][$from_id]['step'] = 'none';
    file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
    $buttons = [];
    foreach ($db['channels'] as $ch) {
        $buttons[] = [['text' => "📢 عضویت در کانال", 'url' => "https://t.me/" . $ch]];
    }
    $buttons[] = [['text' => "✅ بررسی عضویت", 'callback_data' => "check_join"]];
    bot('sendMessage', [
        'chat_id' => $chat_id,
        'text' => "🔒 برای استفاده از ربات lchiikVPN ابتدا باید در کانال‌های زیر عضو شوید:",
        'reply_markup' => json_encode(['inline_keyboard' => $buttons])
    ]);
    exit;
}

// ============ پردازش کالبک ============
if (isset($data) && $data == 'check_join') {
    if (checkJoin($from_id)) {
        bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "🎉 عضویت شما تایید شد! به ربات lchiikVPN خوش آمدید.",
            'reply_markup' => $main_keyboard
        ]);
    } else {
        bot('answerCallbackQuery', [
            'callback_query_id' => $callback_query->id,
            'text' => "❌ هنوز در کانال‌ها عضو نشده‌اید!",
            'show_alert' => true
        ]);
    }
    exit;
}

// ============ پردازش متن ============
if (isset($text)) {
    // ===== استارت =====
    if ($text == '/start') {
        $db['users'][$from_id]['step'] = 'none';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        if (!checkJoin($from_id)) {
            $buttons = [];
            foreach ($db['channels'] as $ch) {
                $buttons[] = [['text' => "📢 عضویت در کانال", 'url' => "https://t.me/" . $ch]];
            }
            $buttons[] = [['text' => "✅ بررسی عضویت", 'callback_data' => "check_join"]];
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "🔒 برای استفاده از ربات lchiikVPN ابتدا باید در کانال‌های زیر عضو شوید:",
                'reply_markup' => json_encode(['inline_keyboard' => $buttons])
            ]);
        } else {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "👋 سلام به ربات lchiikVPN خوش آمدید!\n\nلطفا از منوی زیر گزینه مورد نظر خود را انتخاب کنید 👇",
                'reply_markup' => $main_keyboard
            ]);
        }
    }
    
    // ===== خرید سرویس =====
    elseif ($text == '🛍️ خرید سرویس') {
        if (empty($db['services'])) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "📭 در حال حاضر هیچ سرویسی تعریف نشده است."
            ]);
            exit;
        }
        $inline = [];
        foreach ($db['services'] as $id => $service) {
            $inline[] = [['text' => $service['name'] . " | " . number_format($service['price']) . " ریال", 'callback_data' => "buy_" . $id]];
        }
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "👇 سرویس مورد نظر خود را انتخاب کنید:",
            'reply_markup' => json_encode(['inline_keyboard' => $inline])
        ]);
    }
    
    // ===== سرویس‌های من =====
    elseif ($text == '📦 سرویس‌های من') {
        $myserv = $db['users'][$from_id]['my_services'];
        if (empty($myserv)) {
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "📭 شما هنوز هیچ سرویسی خریداری نکرده‌اید."
            ]);
        } else {
            $txt = "📦 لیست سرویس‌های خریداری شده شما:\n\n";
            foreach ($myserv as $srv) {
                $txt .= "🔹 **سرویس:** {$srv['name']}\n";
                $txt .= "🔑 `{$srv['config']}`\n";
                $txt .= "📅 **تاریخ:** {$srv['date']}\n";
                $txt .= "──────────────────\n";
            }
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => $txt,
                'parse_mode' => 'Markdown'
            ]);
        }
    }
    
    // ===== کیف پول =====
    elseif ($text == '💳 کیف پول') {
        $wallet = number_format($db['users'][$from_id]['wallet']);
        $db['users'][$from_id]['step'] = 'charge_amount';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        
        // دریافت شماره کارت از تنظیمات
        $card_number = isset($db['settings']['card_number']) ? $db['settings']['card_number'] : '5859471029562323';
        $card_holder = isset($db['settings']['card_holder']) ? $db['settings']['card_holder'] : 'عماد صادقی';
        
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "💳 **موجودی فعلی شما:** $wallet ریال\n\n💰 لطفا مبلغی که می‌خواهید به موجودی خود اضافه کنید را به **ریال** و به صورت عدد لاتین ارسال کنید:",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode(['keyboard' => [[['text' => "🔙 بازگشت"]]], 'resize_keyboard' => true])
        ]);
    }
    
    // ===== بازگشت =====
    elseif ($text == '🔙 بازگشت') {
        $db['users'][$from_id]['step'] = 'none';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "🏠 به منوی اصلی بازگشتید.",
            'reply_markup' => $main_keyboard
        ]);
    }
    
    // ===== تماس با پشتیبانی =====
    elseif ($text == '☎️ تماس با پشتیبانی') {
        $db['users'][$from_id]['step'] = 'support';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "☎️ پیام خود را ارسال کنید تا به مدیریت منتقل شود:",
            'reply_markup' => json_encode(['keyboard' => [[['text' => "🔙 بازگشت"]]], 'resize_keyboard' => true])
        ]);
    }
    
    // ===== پنل مدیریت =====
    elseif ($text == '/panel' && $from_id == ADMIN_ID) {
        $db['users'][$from_id]['step'] = 'none';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        $ucount = count($db['users']);
        $scount = count($db['services']);
        $st = $db['status'] == 'on' ? '🟢 روشن' : '🔴 خاموش';
        $p_text = "⚙️ **پنل مدیریت ربات lchiikVPN**\n\n👥 تعداد کاربران: $ucount\n📦 تعداد سرویس‌ها: $scount\nوضعیت ربات: $st";
        $p_keyboard = json_encode([
            'inline_keyboard' => [
                [['text' => "📊 آمار و وضعیت", 'callback_data' => "p_stats"], ['text' => "💡 تغییر وضعیت ربات", 'callback_data' => "p_toggle"]],
                [['text' => "➕ افزودن کانال اجباری", 'callback_data' => "p_addch"], ['text' => "❌ حذف کانال اجباری", 'callback_data' => "p_delch"]],
                [['text' => "➕ ساخت سرویس جدید", 'callback_data' => "p_addsrv"], ['text' => "⚙️ مدیریت سرویس‌ها", 'callback_data' => "p_managesrv"]],
                [['text' => "📢 ارسال پیام همگانی", 'callback_data' => "p_sendall"]],
                [['text' => "💳 تنظیمات پرداخت", 'callback_data' => "p_payment_settings"]]
            ]
        ]);
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => $p_text,
            'parse_mode' => 'Markdown',
            'reply_markup' => $p_keyboard
        ]);
    }
    
    // ===== پاسخ به کاربر =====
    elseif (strpos($text, "/reply_") === 0 && $from_id == ADMIN_ID) {
        $parts = explode("_", $text);
        $target = $parts[1];
        $db['users'][$from_id]['step'] = "replyto_" . $target;
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "✍️ پیام خود را برای کاربر $target ارسال کنید:"
        ]);
    }
    
    // ===== پردازش مرحله کاربر =====
    else {
        $step = $db['users'][$from_id]['step'];
        
        // مرحله شارژ کیف پول
        if ($step == 'charge_amount') {
            if (!is_numeric($text) || $text <= 0) {
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ لطفا یک عدد معتبر ارسال کنید."]);
                exit;
            }
            $db['users'][$from_id]['step'] = 'send_receipt_' . $text;
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            
            $f_amount = number_format($text);
            $card_number = isset($db['settings']['card_number']) ? $db['settings']['card_number'] : '5859471029562323';
            $card_holder = isset($db['settings']['card_holder']) ? $db['settings']['card_holder'] : 'عماد صادقی';
            
            $card_msg = "💳 **درخواست افزایش موجودی**\n\n"
                      . "💵 مبلغ: $f_amount ریال\n\n"
                      . "لطفا مبلغ فوق را به شماره کارت زیر واریز نمایید:\n\n"
                      . "✨ `$card_number` ✨\n"
                      . "👤 **$card_holder**\n\n"
                      . "⚠️ پس از واریز، دکمه **«تایید پرداخت»** را بزنید و در مرحله بعد عکس رسید را بفرستید.";
            
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => $card_msg,
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode([
                    'inline_keyboard' => [[['text' => "✅ تایید پرداخت", 'callback_data' => "confirm_pay"]]]
                ])
            ]);
        }
        
        // مرحله پشتیبانی
        elseif ($step == 'support') {
            bot('sendMessage', [
                'chat_id' => ADMIN_ID,
                'text' => "📬 **پیام جدید پشتیبانی**\n👤 فرستنده: $from_id\n👤 نام: $first_name\n👤 یوزرنیم: @$username\n\n💬 متن پیام:\n$text\n\n📥 جهت پاسخ دادن روی دستور زیر کلیک کنید:\n/reply_$from_id"
            ]);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "✅ پیام شما با موفقیت به پشتیبانی ارسال شد.",
                'reply_markup' => $main_keyboard
            ]);
            $db['users'][$from_id]['step'] = 'none';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        }
        
        // پاسخ ادمین به کاربر
        elseif (strpos($step, 'replyto_') === 0) {
            $target = str_replace('replyto_', '', $step);
            bot('sendMessage', [
                'chat_id' => $target,
                'text' => "☎️ **پاسخ پشتیبانی:**\n\n$text"
            ]);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "✅ پاسخ شما به کاربر $target ارسال شد."
            ]);
            $db['users'][$from_id]['step'] = 'none';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        }
        
        // ===== مدیریت ادمین =====
        elseif ($from_id == ADMIN_ID) {
            // تنظیم شماره کارت
            if ($step == 'p_set_card') {
                $db['settings']['card_number'] = trim($text);
                $db['users'][$from_id]['step'] = 'p_set_card_holder';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ شماره کارت ذخیره شد.\n📝 حالا نام صاحب کارت را وارد کنید:"]);
            }
            
            // تنظیم نام صاحب کارت
            elseif ($step == 'p_set_card_holder') {
                $db['settings']['card_holder'] = trim($text);
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ اطلاعات پرداخت با موفقیت به‌روزرسانی شد!\n\n💳 شماره کارت: " . $db['settings']['card_number'] . "\n👤 صاحب کارت: " . $db['settings']['card_holder']]);
            }
            
            // افزودن کانال
            elseif ($step == 'p_addch_step') {
                $ch = str_replace('@', '', trim($text));
                if (!in_array($ch, $db['channels'])) {
                    $db['channels'][] = $ch;
                    file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                    bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ کانال @$ch با موفقیت اضافه شد."]);
                } else {
                    bot('sendMessage', ['chat_id' => $chat_id, 'text' => "⚠️ این کانال قبلاً اضافه شده است."]);
                }
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            }
            
            // ساخت سرویس جدید - نام
            elseif ($step == 'p_addsrv_name') {
                $new_id = uniqid();
                $db['services'][$new_id] = ['name' => $text, 'price' => 0];
                $db['users'][$from_id]['step'] = 'p_addsrv_price_' . $new_id;
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "💰 اکنون قیمت سرویس را به **ریال** وارد کنید:"]);
            }
            
            // ساخت سرویس جدید - قیمت
            elseif (strpos($step, 'p_addsrv_price_') === 0) {
                $srv_id = str_replace('p_addsrv_price_', '', $step);
                if (!is_numeric($text) || $text < 0) {
                    bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ لطفا قیمت را به صورت عدد معتبر وارد کنید."]);
                    exit;
                }
                $db['services'][$srv_id]['price'] = (int)$text;
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ سرویس با موفقیت ساخته شد. حالا می‌توانید از مدیریت سرویس‌ها برای آن کانفیگ اضافه کنید."]);
            }
            
            // افزودن کانفیگ به سرویس
            elseif (strpos($step, 'p_addconf_') === 0) {
                $srv_id = str_replace('p_addconf_', '', $step);
                if (!isset($db['configs'][$srv_id])) {
                    $db['configs'][$srv_id] = [];
                }
                $db['configs'][$srv_id][] = $text;
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ کانفیگ با موفقیت به این سرویس اضافه شد."]);
            }
            
            // ویرایش قیمت سرویس
            elseif (strpos($step, 'p_editprice_') === 0) {
                $srv_id = str_replace('p_editprice_', '', $step);
                if (!is_numeric($text) || $text < 0) {
                    bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ قیمت نامعتبر است."]);
                    exit;
                }
                $db['services'][$srv_id]['price'] = (int)$text;
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ قیمت سرویس آپدیت شد."]);
            }
            
            // ارسال پیام همگانی
            elseif ($step == 'p_sendall_step') {
                $db['users'][$from_id]['step'] = 'none';
                file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "📢 ارسال پیام همگانی به " . count($db['users']) . " کاربر شروع شد..."]);
                
                $success = 0;
                $failed = 0;
                foreach ($db['users'] as $u_id => $u_data) {
                    $result = bot('sendMessage', ['chat_id' => $u_id, 'text' => $text]);
                    if ($result && isset($result->ok) && $result->ok) {
                        $success++;
                    } else {
                        $failed++;
                    }
                    usleep(50000);
                }
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ پیام همگانی ارسال شد.\n✅ موفق: $success\n❌ ناموفق: $failed"]);
            }
        }
    }
}

// ============ پردازش عکس ============
if (isset($update->message->photo)) {
    $step = $db['users'][$from_id]['step'];
    if (strpos($step, 'receipt_upload_') === 0) {
        $amount = str_replace('receipt_upload_', '', $step);
        $photo = $update->message->photo;
        $file_id = $photo[count($photo) - 1]->file_id;
        
        $db['users'][$from_id]['step'] = 'none';
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => "⏳ رسید شما برای مدیریت ارسال شد. پس از تایید موجودی شما افزایش می‌یابد.",
            'reply_markup' => $main_keyboard
        ]);
        
        $f_amount = number_format($amount);
        bot('sendPhoto', [
            'chat_id' => ADMIN_ID,
            'photo' => $file_id,
            'caption' => "💵 **رسید پرداخت جدید**\n\n👤 کاربر: $from_id\n👤 نام: $first_name\n👤 یوزرنیم: @$username\n💰 مبلغ درخواستی: $f_amount ریال",
            'parse_mode' => 'Markdown',
            'reply_markup' => json_encode([
                'inline_keyboard' => [
                    [['text' => "✅ تایید فاکتور", 'callback_data' => "adm_verify_{$from_id}_{$amount}"], 
                     ['text' => "❌ لغو فاکتور", 'callback_data' => "adm_reject_{$from_id}"]]
                ]
            ])
        ]);
    }
}

// ============ پردازش کالبک‌ها ============
if (isset($data)) {
    // ===== تایید پرداخت =====
    if ($data == 'confirm_pay') {
        $step = $db['users'][$from_id]['step'];
        if (strpos($step, 'send_receipt_') === 0) {
            $amount = str_replace('send_receipt_', '', $step);
            $db['users'][$from_id]['step'] = 'receipt_upload_' . $amount;
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "📸 لطفا عکس رسید واریزی خود را ارسال کنید:"
            ]);
        }
    }
    
    // ===== تایید فاکتور توسط ادمین =====
    elseif (strpos($data, 'adm_verify_') === 0) {
        $ex = explode("_", $data);
        $u_id = $ex[2];
        $amount = $ex[3];
        
        if (!isset($db['users'][$u_id])) {
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ کاربر یافت نشد!"]);
            exit;
        }
        
        $db['users'][$u_id]['wallet'] += (int)$amount;
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        
        bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
        bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ حساب کاربر $u_id به مبلغ " . number_format($amount) . " ریال شارژ شد."]);
        
        $f_amount = number_format($amount);
        bot('sendMessage', [
            'chat_id' => $u_id,
            'text' => "🎉 **فاکتور تایید شد!**\n\n💰 مبلغ $f_amount ریال با موفقیت به حساب شما اضافه شد.\n💳 موجودی جدید: " . number_format($db['users'][$u_id]['wallet']) . " ریال"
        ]);
    }
    
    // ===== رد فاکتور توسط ادمین =====
    elseif (strpos($data, 'adm_reject_') === 0) {
        $ex = explode("_", $data);
        $u_id = $ex[2];
        
        bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
        bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ فاکتور کاربر $u_id رد شد."]);
        
        bot('sendMessage', [
            'chat_id' => $u_id,
            'text' => "🔴 **فاکتور لغو شد!**\n\nپرداخت شما توسط مدیریت تایید نشد و پولی به حساب شما واریز نگردید.\n\nلطفا در صورت نیاز با پشتیبانی تماس بگیرید."
        ]);
    }
    
    // ===== خرید سرویس =====
    elseif (strpos($data, 'buy_') === 0) {
        $srv_id = str_replace('buy_', '', $data);
        if (!isset($db['services'][$srv_id])) {
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ سرویس یافت نشد."]);
            exit;
        }
        $service = $db['services'][$srv_id];
        $price = $service['price'];
        $user_wallet = $db['users'][$from_id]['wallet'];
        
        if ($user_wallet < $price) {
            bot('answerCallbackQuery', [
                'callback_query_id' => $callback_query->id,
                'text' => "❌ موجودی کافی نیست!",
                'show_alert' => true
            ]);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "❌ **موجودی شما کافی نیست!**\n\n💰 قیمت سرویس: " . number_format($price) . " ریال\n💳 موجودی شما: " . number_format($user_wallet) . " ریال\n\nلطفا ابتدا حساب خود را شارژ کنید."
            ]);
            exit;
        }
        
        if (empty($db['configs'][$srv_id])) {
            bot('answerCallbackQuery', [
                'callback_query_id' => $callback_query->id,
                'text' => "❌ کانفیگ موجود نیست!",
                'show_alert' => true
            ]);
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "📭 متاسفانه در حال حاضر کانفیگ موجودی برای این سرویس وجود ندارد. لطفا به پشتیبانی پیام دهید."]);
            exit;
        }
        
        $config = array_shift($db['configs'][$srv_id]);
        if (empty($db['configs'][$srv_id])) {
            unset($db['configs'][$srv_id]);
        }
        
        $db['users'][$from_id]['wallet'] -= $price;
        
        $srv_info = [
            'name' => $service['name'],
            'config' => $config,
            'date' => date('Y-m-d H:i')
        ];
        $db['users'][$from_id]['my_services'][] = $srv_info;
        file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
        
        bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
        
        $bill = "🛍️ **فاکتور خرید موفق lchiikVPN**\n\n"
              . "📦 **سرویس:** {$service['name']}\n"
              . "💰 **مبلغ کسر شده:** " . number_format($price) . " ریال\n"
              . "💳 **باقیمانده کیف پول:** " . number_format($db['users'][$from_id]['wallet']) . " ریال\n"
              . "──────────────────\n"
              . "🔑 **کانفیگ اختصاصی شما:**\n\n"
              . "`$config`\n\n"
              . "✨ از خرید شما سپاسگزاریم! کانفیگ در منوی سرویس‌های من نیز ذخیره شد.";
              
        bot('sendMessage', [
            'chat_id' => $chat_id,
            'text' => $bill,
            'parse_mode' => 'Markdown'
        ]);
    }
    
    // ===== پنل مدیریت - کالبک‌ها =====
    elseif ($from_id == ADMIN_ID) {
        // آمار
        if ($data == 'p_stats') {
            $ucount = count($db['users']);
            $scount = count($db['services']);
            $ccount = 0;
            foreach ($db['configs'] as $configs) {
                $ccount += count($configs);
            }
            $st = $db['status'] == 'on' ? '🟢 روشن' : '🔴 خاموش';
            bot('answerCallbackQuery', [
                'callback_query_id' => $callback_query->id,
                'text' => "📊 آمار:\n👥 کاربران: $ucount\n📦 سرویس‌ها: $scount\n🔑 کانفیگ‌ها: $ccount\nوضعیت: $st",
                'show_alert' => true
            ]);
        }
        
        // تغییر وضعیت
        elseif ($data == 'p_toggle') {
            $db['status'] = ($db['status'] == 'on') ? 'off' : 'on';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('answerCallbackQuery', [
                'callback_query_id' => $callback_query->id,
                'text' => "وضعیت ربات تغییر کرد به: " . ($db['status'] == 'on' ? '🟢 روشن' : '🔴 خاموش'),
                'show_alert' => true
            ]);
        }
        
        // تنظیمات پرداخت
        elseif ($data == 'p_payment_settings') {
            $card_number = isset($db['settings']['card_number']) ? $db['settings']['card_number'] : '5859471029562323';
            $card_holder = isset($db['settings']['card_holder']) ? $db['settings']['card_holder'] : 'عماد صادقی';
            
            $text_settings = "💳 **تنظیمات پرداخت**\n\n"
                           . "🏦 شماره کارت: `$card_number`\n"
                           . "👤 صاحب کارت: $card_holder\n\n"
                           . "برای تغییر اطلاعات، دکمه زیر را بزنید:";
            
            $inline = [
                [['text' => "✏️ تغییر شماره کارت", 'callback_data' => "p_edit_card"]],
                [['text' => "🔙 بازگشت به پنل", 'callback_data' => "p_back_to_panel"]]
            ];
            
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => $text_settings,
                'parse_mode' => 'Markdown',
                'reply_markup' => json_encode(['inline_keyboard' => $inline])
            ]);
        }
        
        // ویرایش شماره کارت
        elseif ($data == 'p_edit_card') {
            $db['users'][$from_id]['step'] = 'p_set_card';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => "✏️ شماره کارت جدید را وارد کنید (۱۶ رقمی):"
            ]);
        }
        
        // بازگشت به پنل
        elseif ($data == 'p_back_to_panel') {
            $ucount = count($db['users']);
            $scount = count($db['services']);
            $st = $db['status'] == 'on' ? '🟢 روشن' : '🔴 خاموش';
            $p_text = "⚙️ **پنل مدیریت ربات lchiikVPN**\n\n👥 تعداد کاربران: $ucount\n📦 تعداد سرویس‌ها: $scount\nوضعیت ربات: $st";
            $p_keyboard = json_encode([
                'inline_keyboard' => [
                    [['text' => "📊 آمار و وضعیت", 'callback_data' => "p_stats"], ['text' => "💡 تغییر وضعیت ربات", 'callback_data' => "p_toggle"]],
                    [['text' => "➕ افزودن کانال اجباری", 'callback_data' => "p_addch"], ['text' => "❌ حذف کانال اجباری", 'callback_data' => "p_delch"]],
                    [['text' => "➕ ساخت سرویس جدید", 'callback_data' => "p_addsrv"], ['text' => "⚙️ مدیریت سرویس‌ها", 'callback_data' => "p_managesrv"]],
                    [['text' => "📢 ارسال پیام همگانی", 'callback_data' => "p_sendall"]],
                    [['text' => "💳 تنظیمات پرداخت", 'callback_data' => "p_payment_settings"]]
                ]
            ]);
            bot('sendMessage', [
                'chat_id' => $chat_id,
                'text' => $p_text,
                'parse_mode' => 'Markdown',
                'reply_markup' => $p_keyboard
            ]);
        }
        
        // افزودن کانال
        elseif ($data == 'p_addch') {
            $db['users'][$from_id]['step'] = 'p_addch_step';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "📣 آیدی کانال را بدون @ ارسال کنید:"]);
        }
        
        // حذف کانال
        elseif ($data == 'p_delch') {
            if (empty($db['channels'])) {
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ هیچ کانالی تعریف نشده است."]);
                exit;
            }
            $inline = [];
            foreach ($db['channels'] as $ch) {
                $inline[] = [['text' => "@" . $ch, 'callback_data' => "p_removech_" . $ch]];
            }
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ کانالی که می‌خواهید حذف شود را انتخاب کنید:", 'reply_markup' => json_encode(['inline_keyboard' => $inline])]);
        }
        
        // حذف کانال - اجرا
        elseif (strpos($data, 'p_removech_') === 0) {
            $ch = str_replace('p_removech_', '', $data);
            $db['channels'] = array_values(array_diff($db['channels'], [$ch]));
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('deleteMessage', ['chat_id' => $chat_id, 'message_id' => $message_id]);
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ کانال @$ch حذف شد."]);
        }
        
        // ساخت سرویس جدید
        elseif ($data == 'p_addsrv') {
            $db['users'][$from_id]['step'] = 'p_addsrv_name';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "📝 نام سرویس جدید را وارد کنید (مثلا: مولتی لوکیشن):"]);
        }
        
        // مدیریت سرویس‌ها
        elseif ($data == 'p_managesrv') {
            if (empty($db['services'])) {
                bot('sendMessage', ['chat_id' => $chat_id, 'text' => "❌ هیچ سرویسی وجود ندارد."]);
                exit;
            }
            $inline = [];
            foreach ($db['services'] as $id => $srv) {
                $inline[] = [['text' => $srv['name'], 'callback_data' => "p_srvopt_" . $id]];
            }
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "⚙️ سرویس مورد نظر را برای مدیریت انتخاب کنید:", 'reply_markup' => json_encode(['inline_keyboard' => $inline])]);
        }
        
        // گزینه‌های سرویس
        elseif (strpos($data, 'p_srvopt_') === 0) {
            $srv_id = str_replace('p_srvopt_', '', $data);
            $srv = $db['services'][$srv_id];
            $ccount = isset($db['configs'][$srv_id]) ? count($db['configs'][$srv_id]) : 0;
            
            $text_opt = "📦 **سرویس:** {$srv['name']}\n💰 **قیمت:** " . number_format($srv['price']) . " ریال\n🔋 **تعداد کانفیگ موجود:** $ccount";
            $inline = [
                [['text' => "➕ افزودن کانفیگ", 'callback_data' => "p_addconf_" . $srv_id], ['text' => "🗑️ حذف کانفیگ‌ها", 'callback_data' => "p_clearconf_" . $srv_id]],
                [['text' => "💵 تغییر قیمت", 'callback_data' => "p_editprice_" . $srv_id], ['text' => "❌ حذف کل سرویس", 'callback_data' => "p_delsrv_" . $srv_id]]
            ];
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => $text_opt, 'parse_mode' => 'Markdown', 'reply_markup' => json_encode(['inline_keyboard' => $inline])]);
        }
        
        // افزودن کانفیگ
        elseif (strpos($data, 'p_addconf_') === 0) {
            $srv_id = str_replace('p_addconf_', '', $data);
            $db['users'][$from_id]['step'] = 'p_addconf_' . $srv_id;
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "🔑 متن کانفیگ (V2ray Link) را ارسال کنید:"]);
        }
        
        // پاک کردن کانفیگ‌ها
        elseif (strpos($data, 'p_clearconf_') === 0) {
            $srv_id = str_replace('p_clearconf_', '', $data);
            $db['configs'][$srv_id] = [];
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ تمامی کانفیگ‌های این سرویس پاک شدند."]);
        }
        
        // ویرایش قیمت
        elseif (strpos($data, 'p_editprice_') === 0) {
            $srv_id = str_replace('p_editprice_', '', $data);
            $db['users'][$from_id]['step'] = 'p_editprice_' . $srv_id;
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "💰 قیمت جدید را به **ریال** بفرستید:"]);
        }
        
        // حذف سرویس
        elseif (strpos($data, 'p_delsrv_') === 0) {
            $srv_id = str_replace('p_delsrv_', '', $data);
            unset($db['services'][$srv_id]);
            unset($db['configs'][$srv_id]);
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "✅ سرویس به طور کامل حذف شد."]);
        }
        
        // ارسال پیام همگانی
        elseif ($data == 'p_sendall') {
            $db['users'][$from_id]['step'] = 'p_sendall_step';
            file_put_contents($db_file, json_encode($db, JSON_PRETTY_PRINT));
            bot('sendMessage', ['chat_id' => $chat_id, 'text' => "📢 متن پیام همگانی خود را ارسال کنید:"]);
        }
    }
}

echo "OK";
?>
