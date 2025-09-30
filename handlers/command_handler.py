"""
Command Handler for Telegram bot commands.

Handles all bot commands:
- /start - Welcome message
- /help - Help and instructions
- /summarize - Create summary (with options)
- /mysummaries - Show saved summaries
- /search - Search in summaries
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    Application,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

from database.models import User
from services.summarizer import MessageSummarizer
from config import settings

logger = logging.getLogger(__name__)


# ============== /start Command ==============

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    
    Sends welcome message with bot features and instructions.
    """
    user = update.effective_user
    chat = update.effective_chat
    
    try:
        # Update user in database
        await _update_user(user)
        
        # Check if in private chat or group
        if chat.type == 'private':
            welcome_text = f"""
👋 שלום {user.first_name}!

אני בוט סיכום שיחות חכם 🤖

🎯 **מה אני יכול לעשות?**
• סיכום אוטומטי של שיחות בקבוצות
• שמירת עד 5 סיכומים אחרונים
• חיפוש בסיכומים שמורים
• סוגי סיכום שונים (מהיר, מפורט, החלטות, שאלות)

📌 **איך להשתמש?**
1. הוסף אותי לקבוצה
2. בקבוצה, כתוב: `/summarize`
3. הסיכום ישמר אצלך בצ'אט הפרטי!

💡 **פקודות נוספות:**
/help - עזרה מפורטת
/mysummaries - הצג את הסיכומים שלי
/search - חפש בסיכומים

בוא נתחיל! 🚀
"""
        else:
            # In group chat
            welcome_text = f"""
👋 היי! אני בוט סיכום שיחות.

כדי לסכם את השיחה כאן, כתבו:
/summarize

או לחצו על /help למידע נוסף.
"""
        
        await update.message.reply_text(
            text=welcome_text,
            parse_mode=ParseMode.MARKDOWN,
        )
        
        logger.info(f"Start command from user {user.id} in chat {chat.id}")
        
    except Exception as e:
        logger.error(f"Error in /start command: {e}", exc_info=True)
        await update.message.reply_text(
            "אופס! משהו השתבש. נסה שוב מאוחר יותר."
        )


# ============== /help Command ==============

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.
    
    Sends detailed help message with all available commands and features.
    """
    help_text = """
📚 **מדריך שימוש מלא**

🔹 **פקודות בסיסיות:**

`/summarize` - סיכום ה-50 הודעות האחרונות
`/summarize 20` - סיכום 20 הודעות אחרונות
`/summarize 100` - סיכום 100 הודעות אחרונות

🔹 **סוגי סיכום:**

`/summarize quick` - סיכום מהיר (2-3 נקודות)
`/summarize detailed` - סיכום מפורט (8-10 נקודות)
`/summarize decisions` - רק החלטות שהתקבלו
`/summarize questions` - שאלות פתוחות

🔹 **שילוב אופציות:**

`/summarize 30 quick` - 30 הודעות, סיכום מהיר
`/summarize 100 detailed` - 100 הודעות, מפורט
`/summarize decisions` - כל הבאפר, רק החלטות

🔹 **ניהול סיכומים:**

`/mysummaries` - הצג 5 סיכומים אחרונים
`/search <מילה>` - חפש בסיכומים
דוגמה: `/search פגישה`

🔹 **תכונות מיוחדות:**

• 📌 כפתור "שמור סיכום" - שומר בצ'אט הפרטי
• 🔄 עד 5 סיכומים נשמרים תמיד
• 🧹 סיכומים ישנים נמחקים אוטומטית
• 🎯 ניקוי הבאפר לאחר כל סיכום

💡 **טיפים:**
- הבוט שומר את 50 ההודעות האחרונות בזיכרון
- ניתן לסכם בין 10 ל-200 הודעות
- הסיכומים נשמרים רק אצלך בפרטי

יש שאלות? כתוב לנו! 😊
"""
    
    await update.message.reply_text(
        text=help_text,
        parse_mode=ParseMode.MARKDOWN,
    )
    
    logger.info(f"Help command from user {update.effective_user.id}")


# ============== /summarize Command ==============

async def handle_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /summarize command with all options.
    
    Syntax:
    /summarize - summarize buffer (50 messages)
    /summarize 30 - summarize 30 messages
    /summarize quick - quick summary
    /summarize 50 detailed - 50 messages, detailed
    /summarize decisions - only decisions
    """
    user = update.effective_user
    chat = update.effective_chat
    
    # Only work in groups
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "⚠️ פקודה זו פועלת רק בקבוצות!\n"
            "הוסף אותי לקבוצה ונסה שם."
        )
        return
    
    try:
        # Update user
        await _update_user(user)
        
        # Parse command arguments
        args = context.args
        message_count = None
        summary_type = "standard"
        
        # Parse arguments
        for arg in args:
            if arg.isdigit():
                # Number of messages
                count = int(arg)
                if 10 <= count <= 200:
                    message_count = count
                else:
                    await update.message.reply_text(
                        "⚠️ מספר ההודעות חייב להיות בין 10 ל-200"
                    )
                    return
            elif arg.lower() in ['quick', 'detailed', 'decisions', 'questions']:
                # Summary type
                summary_type = arg.lower()
        
        # Send "processing" message
        processing_msg = await update.message.reply_text(
            "⏳ יוצר סיכום... רגע אחד..."
        )
        
        # Create summary
        summarizer = MessageSummarizer()
        result = await summarizer.summarize_chat(
            chat_id=chat.id,
            user_telegram_id=user.id,
            message_count=message_count,
            summary_type=summary_type,
            language="he",
            chat_title=chat.title,
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        if not result["success"]:
            await update.message.reply_text(
                f"❌ שגיאה ביצירת הסיכום:\n{result.get('error', 'שגיאה לא ידועה')}"
            )
            return
        
        # Format summary message
        summary_text = result["summary_text"]
        message_count_text = result["message_count"]
        
        # Get summary type emoji
        type_emoji = {
            "standard": "📌",
            "quick": "⚡",
            "detailed": "📋",
            "decisions": "✅",
            "questions": "❓",
        }.get(summary_type, "📌")
        
        full_message = (
            f"{type_emoji} **סיכום השיחה** ({message_count_text} הודעות)\n\n"
            f"{summary_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💡 לחץ על הכפתור למטה לשמירה בצ'אט הפרטי"
        )
        
        # Create inline keyboard with "Save" button
        keyboard = [
            [
                InlineKeyboardButton(
                    "📌 שמור סיכום",
                    callback_data=f"save_summary:{result['summary_id']}"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send summary to group
        await update.message.reply_text(
            text=full_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
        
        logger.info(
            f"Summary created by user {user.id} in chat {chat.id}: "
            f"{message_count_text} messages, type: {summary_type}"
        )
        
    except Exception as e:
        logger.error(f"Error in /summarize command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ אופס! משהו השתבש ביצירת הסיכום.\n"
            "נסה שוב או פנה לתמיכה."
        )


# ============== /mysummaries Command ==============

async def handle_mysummaries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /mysummaries command.
    
    Shows user's last 5 saved summaries.
    """
    user = update.effective_user
    chat = update.effective_chat
    
    # Only work in private chat
    if chat.type != 'private':
        await update.message.reply_text(
            "⚠️ פקודה זו פועלת רק בצ'אט הפרטי!\n"
            "שלח לי הודעה פרטית ונסה שם."
        )
        return
    
    try:
        # Get user's summaries
        summarizer = MessageSummarizer()
        summaries = await summarizer.get_user_summaries(
            user_telegram_id=user.id,
            limit=5,
        )
        
        if not summaries:
            await update.message.reply_text(
                "📭 אין לך סיכומים שמורים עדיין.\n\n"
                "💡 כדי לשמור סיכום:\n"
                "1. הוסף אותי לקבוצה\n"
                "2. כתוב `/summarize` בקבוצה\n"
                "3. לחץ על הכפתור 'שמור סיכום'"
            )
            return
        
        # Format summaries list
        message_parts = ["📚 **הסיכומים שלך** (5 אחרונים):\n"]
        
        for i, summary in enumerate(summaries, 1):
            date_str = summary.created_at.strftime("%d/%m/%Y %H:%M")
            chat_name = summary.chat_title or "קבוצה ללא שם"
            
            # Get summary type emoji
            type_emoji = {
                "standard": "📌",
                "quick": "⚡",
                "detailed": "📋",
                "decisions": "✅",
                "questions": "❓",
            }.get(summary.summary_type, "📌")
            
            message_parts.append(
                f"\n{i}. {type_emoji} **{chat_name}**\n"
                f"   📅 {date_str}\n"
                f"   💬 {summary.message_count} הודעות\n"
            )
        
        message_parts.append(
            "\n━━━━━━━━━━━━━━━━━━\n"
            "💡 להצגת סיכום מסוים, לחץ על המספר שלו\n"
            "🔍 לחיפוש: `/search <מילה>`"
        )
        
        # Create keyboard with summary buttons
        keyboard = []
        for i, summary in enumerate(summaries, 1):
            keyboard.append([
                InlineKeyboardButton(
                    f"{i}. הצג סיכום",
                    callback_data=f"show_summary:{summary.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text="".join(message_parts),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
        
        logger.info(f"User {user.id} viewed their summaries ({len(summaries)} found)")
        
    except Exception as e:
        logger.error(f"Error in /mysummaries command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ שגיאה בטעינת הסיכומים.\nנסה שוב מאוחר יותר."
        )


# ============== /search Command ==============

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /search command.
    
    Search in user's saved summaries.
    Syntax: /search <search_term>
    """
    user = update.effective_user
    chat = update.effective_chat
    
    # Only work in private chat
    if chat.type != 'private':
        await update.message.reply_text(
            "⚠️ פקודה זו פועלת רק בצ'אט הפרטי!\n"
            "שלח לי הודעה פרטית ונסה שם."
        )
        return
    
    # Check if search term provided
    if not context.args:
        await update.message.reply_text(
            "🔍 **חיפוש בסיכומים**\n\n"
            "שימוש: `/search <מילת חיפוש>`\n\n"
            "דוגמאות:\n"
            "• `/search פגישה`\n"
            "• `/search תקציב`\n"
            "• `/search החלטה`"
        )
        return
    
    try:
        # Get search term
        search_term = " ".join(context.args)
        
        # Search summaries
        summarizer = MessageSummarizer()
        results = await summarizer.search_summaries(
            user_telegram_id=user.id,
            search_term=search_term,
        )
        
        if not results:
            await update.message.reply_text(
                f"🔍 לא נמצאו תוצאות עבור: **{search_term}**\n\n"
                f"נסה מילת חיפוש אחרת או הצג את כל הסיכומים עם `/mysummaries`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        
        # Format results
        message_parts = [
            f"🔍 **תוצאות חיפוש עבור:** {search_term}\n"
            f"נמצאו {len(results)} תוצאות:\n"
        ]
        
        for i, summary in enumerate(results[:5], 1):  # Show max 5 results
            date_str = summary.created_at.strftime("%d/%m/%Y %H:%M")
            chat_name = summary.chat_title or "קבוצה ללא שם"
            
            message_parts.append(
                f"\n{i}. **{chat_name}**\n"
                f"   📅 {date_str}\n"
                f"   💬 {summary.message_count} הודעות\n"
            )
        
        # Create keyboard
        keyboard = []
        for i, summary in enumerate(results[:5], 1):
            keyboard.append([
                InlineKeyboardButton(
                    f"{i}. הצג סיכום",
                    callback_data=f"show_summary:{summary.id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text="".join(message_parts),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
        )
        
        logger.info(
            f"User {user.id} searched for '{search_term}', "
            f"found {len(results)} results"
        )
        
    except Exception as e:
        logger.error(f"Error in /search command: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ שגיאה בחיפוש.\nנסה שוב מאוחר יותר."
        )


# ============== Callback Query Handlers ==============

async def handle_save_summary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Save Summary" button callback.
    
    Sends the summary to user's private chat.
    """
    query = update.callback_query
    user = query.from_user
    
    try:
        # Parse callback data
        callback_data = query.data
        summary_id = callback_data.split(":")[1]
        
        # Get summary from database
        from database.models import Summary
        summary = await Summary.get(summary_id)
        
        if not summary:
            await query.answer("❌ סיכום לא נמצא", show_alert=True)
            return
        
        # Send summary to private chat
        summary_message = (
            f"📌 **סיכום שמור**\n\n"
            f"📍 מקבוצה: {summary.chat_title or 'קבוצה'}\n"
            f"📅 תאריך: {summary.created_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"💬 {summary.message_count} הודעות\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{summary.summary_text}"
        )
        
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=summary_message,
                parse_mode=ParseMode.MARKDOWN,
            )
            
            # Answer callback
            await query.answer(
                "✅ הסיכום נשמר בצ'אט הפרטי!",
                show_alert=False,
            )
            
            logger.info(f"Summary {summary_id} sent to user {user.id}")
            
        except Exception as e:
            # User hasn't started private chat with bot
            await query.answer(
                "⚠️ לא ניתן לשלוח הודעה פרטית.\n"
                "שלח לי הודעה /start בפרטי קודם!",
                show_alert=True,
            )
            logger.warning(f"Cannot send message to user {user.id}: {e}")
        
    except Exception as e:
        logger.error(f"Error in save summary callback: {e}", exc_info=True)
        await query.answer(
            "❌ שגיאה בשמירת הסיכום",
            show_alert=True,
        )


async def handle_show_summary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle "Show Summary" button callback.
    
    Shows the full summary text.
    """
    query = update.callback_query
    
    try:
        # Parse callback data
        callback_data = query.data
        summary_id = callback_data.split(":")[1]
        
        # Get summary from database
        from database.models import Summary
        summary = await Summary.get(summary_id)
        
        if not summary:
            await query.answer("❌ סיכום לא נמצא", show_alert=True)
            return
        
        # Format summary
        summary_message = (
            f"📌 **סיכום מלא**\n\n"
            f"📍 מקבוצה: {summary.chat_title or 'קבוצה'}\n"
            f"📅 {summary.created_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"💬 {summary.message_count} הודעות\n"
            f"🏷️ סוג: {summary.summary_type}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"{summary.summary_text}"
        )
        
        # Send as new message
        await query.message.reply_text(
            text=summary_message,
            parse_mode=ParseMode.MARKDOWN,
        )
        
        # Answer callback
        await query.answer()
        
        logger.info(f"Summary {summary_id} displayed to user {query.from_user.id}")
        
    except Exception as e:
        logger.error(f"Error in show summary callback: {e}", exc_info=True)
        await query.answer(
            "❌ שגיאה בהצגת הסיכום",
            show_alert=True,
        )


# ============== Helper Functions ==============

async def _update_user(user) -> User:
    """
    Update or create user in database.
    
    Args:
        user: Telegram user object
        
    Returns:
        User: Updated/created user document
    """
    try:
        db_user = await User.find_one(User.telegram_id == user.id)
        
        if db_user:
            db_user.username = user.username
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.language_code = user.language_code
            db_user.is_bot = user.is_bot
            db_user.last_interaction = datetime.utcnow()
            db_user.updated_at = datetime.utcnow()
            await db_user.save()
        else:
            db_user = User(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                is_bot=user.is_bot,
                last_interaction=datetime.utcnow(),
            )
            await db_user.insert()
            logger.info(f"New user registered: {user.id} (@{user.username})")
        
        return db_user
        
    except Exception as e:
        logger.error(f"Error updating user {user.id}: {e}")
        raise


# ============== Setup Function ==============

def setup_command_handlers(application: Application):
    """
    Register all command handlers with the application.
    
    Args:
        application: Telegram bot application
    """
    # Basic commands
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_help))
    
    # Main commands
    application.add_handler(CommandHandler("summarize", handle_summarize))
    application.add_handler(CommandHandler("mysummaries", handle_mysummaries))
    application.add_handler(CommandHandler("search", handle_search))
    
    # Callback query handlers for inline buttons
    application.add_handler(
        CallbackQueryHandler(
            handle_save_summary_callback,
            pattern="^save_summary:"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_show_summary_callback,
            pattern="^show_summary:"
        )
    )
    
    logger.info("Command handlers registered")
