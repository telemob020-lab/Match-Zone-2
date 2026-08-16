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
                "⚽ Today's Matches",
                callback_data="today_matches",
            )
        ],
        [
            InlineKeyboardButton(
                "🏆 Daily Challenge",
                callback_data="daily_challenge",
            )
        ],
        [
            InlineKeyboardButton(
                "📊 My Stats",
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
        "⚽ <b>Welcome to Match Zone!</b>\n\n"
        "Your daily football companion 👋\n\n"
        "Follow today's matches, test your football knowledge, "
        "and enjoy interactive challenges.\n\n"
        "Choose an option below:"
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
        return "⚽ There are no matches available today."

    text = "⚽ <b>Today's Matches</b>\n\n"

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
            status_text = "🔴 LIVE"
        elif status in ["FT", "AET", "PEN"]:
            status_text = "✅ Finished"
        else:
            status_text = status

        text += (
            f"🏆 <b>{league}</b>\n"
            f"⚽ {home} vs {away}\n"
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

    # =========================
    # Today's Matches
    # =========================

    if query.data == "today_matches":

        await query.edit_message_text(
            "⏳ Loading today's matches..."
        )

        try:

            data = get_today_matches()

            text = format_matches(data)

            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔄 Refresh",
                        callback_data="today_matches",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Main Menu",
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
                "❌ Unable to load matches right now.\n"
                "Please try again later."
            )

        except Exception as error:

            logger.exception("Unexpected error: %s", error)

            await query.edit_message_text(
                "❌ Something went wrong.\n"
                "Please try again later."
            )

    # =========================
    # Daily Challenge
    # =========================

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
                    "🔙 Main Menu",
                    callback_data="home",
                )
            ],
        ]

        await query.edit_message_text(
            "🏆 <b>Daily Challenge</b>\n\n"
            "Who is the all-time top scorer in UEFA Champions League history?\n\n"
            "Choose your answer:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # =========================
    # Correct Answer
    # =========================

    elif query.data == "answer_correct":

        await query.edit_message_text(
            "🎉 <b>Correct Answer!</b>\n\n"
            "🔥 Great job! You earned 1 point.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Main Menu",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # =========================
    # Wrong Answer
    # =========================

    elif query.data == "answer_wrong":

        await query.edit_message_text(
            "❌ <b>Wrong Answer!</b>\n\n"
            "Better luck next time! ⚽",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Main Menu",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # =========================
    # Stats
    # =========================

    elif query.data == "stats":

        await query.edit_message_text(
            "📊 <b>Your Stats</b>\n\n"
            "🏆 Points: 0\n"
            "🔥 Daily Streak: 0\n"
            "🎯 Correct Answers: 0",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 Main Menu",
                            callback_data="home",
                        )
                    ]
                ]
            ),
        )

    # =========================
    # Home
    # =========================

    elif query.data == "home":

        await query.edit_message_text(
            "⚽ <b>Match Zone</b>\n\n"
            "Welcome back! 👋\n\n"
            "Choose an option below:",
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
