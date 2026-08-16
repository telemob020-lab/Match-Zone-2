import os
import logging
from datetime import datetime

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# Configuration
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")

API_URL = "https://v3.football.api-sports.io"

# =========================
# Logging
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================
# Main Menu
# =========================

def main_menu():
    keyboard = [
        [
            InlineKeyboardButton(
                "⚽ مباريات اليوم",
                callback_data="today_matches",
            )
        ],
        [
            InlineKeyboardButton(
                "🏆 تحدي اليوم",
                callback_data="daily_challenge",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 الإحصائيات",
                callback_data="stats",
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# Start Command
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚽ <b>Match Zone</b>\n\n"
        "مرحباً بك في Match Zone 👋\n\n"
        "تابع مباريات اليوم واختبر معلوماتك الرياضية.\n\n"
        "اختر من القائمة:"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# API-Football
# =========================

def get_today_matches():
    today = datetime.now().strftime("%Y-%m-%d")

    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    params = {
        "date": today
    }

    response = requests.get(
        f"{API_URL}/fixtures",
        headers=headers,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


# =========================
# Format Matches
# =========================

def format_matches(data):
    matches = data.get("response", [])

    if not matches:
        return "⚽ لا توجد مباريات متاحة اليوم."

    text = "⚽ <b>مباريات اليوم</b>\n\n"

    for match in matches[:20]:

        league = match["league"]["name"]

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        date_time = match["fixture"]["date"]

        try:
            dt = datetime.fromisoformat(
                date_time.replace("Z", "+00:00")
            )

            match_time = dt.strftime("%H:%M")

        except Exception:
            match_time = "--:--"

        status = match["fixture"]["status"]["short"]

        if status == "NS":
            status_text = f"🕐 {match_time}"
        elif status in ["1H", "2H", "HT", "ET", "P"]:
            status_text = "🔴 مباشر"
        elif status in ["FT", "AET", "PEN"]:
            status_text = "✅ انتهت"
        else:
            status_text = status

        text += (
            f"🏆 <b>{league}</b>\n"
            f"⚽ {home} × {away}\n"
            f"{status_text}\n\n"
        )

    return text


# =========================
# Button Handler
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    await query.answer()

    # -------------------------
    # Today's Matches
    # -------------------------

    if query.data == "today_matches":

        await query.edit_message_text(
            "⏳ جاري تحميل مباريات اليوم..."
        )

        try:

            data = get_today_matches()

            text = format_matches(data)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 تحديث",
                        callback_data="today_matches",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 القائمة الرئيسية",
                        callback_data="home",
                    )
                ],
            ]

            await query.edit_message_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except requests.RequestException as error:

            logger.error("API error: %s", error)

            await query.edit_message_text(
                "❌ تعذر تحميل المباريات حالياً.\n"
                "حاول مرة أخرى بعد قليل."
            )

        except Exception as error:

            logger.exception("Unexpected error: %s", error)

            await query.edit_message_text(
                "❌ حدث خطأ غير متوقع."
            )

    # -------------------------
    # Daily Challenge
    # -------------------------

    elif query.data == "daily_challenge":

        keyboard = [
            [
                InlineKeyboardButton(
                    "Cristiano Ronaldo",
                    callback_data="answer_correct",
                )
            ],
            [
                InlineKeyboardButton(
                    "Lionel Messi",
                    callback_data="answer_wrong",
                )
            ],
            [
                InlineKeyboardButton(
                    "Robert Lewandowski",
                    callback_data="answer_wrong",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 الرئيسية",
                    callback_data="home",
                )
            ],
        ]

        await query.edit_message_text(
            "🏆 <b>تحدي اليوم</b>\n\n"
            "من هو الهداف التاريخي لدوري أبطال أوروبا؟",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # -------------------------
    # Correct Answer
    # -------------------------

    elif query.data == "answer_correct":

        await query.edit_message_text(
            "🎉 <b>إجابة صحيحة!</b>\n\n"
            "🔥 أحسنت! حصلت على نقطة.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 القائمة الرئيسية",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # -------------------------
    # Wrong Answer
    # -------------------------

    elif query.data == "answer_wrong":

        await query.edit_message_text(
            "❌ إجابة غير صحيحة.\n\n"
            "حاول في تحدي اليوم القادم! ⚽",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 القائمة الرئيسية",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # -------------------------
    # Stats
    # -------------------------

    elif query.data == "stats":

        await query.edit_message_text(
            "📊 <b>إحصائياتك</b>\n\n"
            "🏆 النقاط: 0\n"
            "🔥 سلسلة الأيام: 0\n"
            "🎯 الإجابات الصحيحة: 0",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 القائمة الرئيسية",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # -------------------------
    # Home
    # -------------------------

    elif query.data == "home":

        await query.edit_message_text(
            "⚽ <b>Match Zone</b>\n\n"
            "اختر من القائمة:",
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# Main
# =========================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is missing."
        )

    if not API_FOOTBALL_KEY:
        raise RuntimeError(
            "API_FOOTBALL_KEY environment variable is missing."
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    logger.info("Match Zone is starting...")

    application.run_polling()


if __name__ == "__main__":
    main()
