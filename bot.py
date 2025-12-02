"""Main entry point for the Telegram bot."""
from datetime import time
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, logger
from services import AIService, StorageService
from handlers import BotHandlers


def main():
    """Initialize and run the bot."""
    # Initialize services
    ai_service = AIService(OPENAI_API_KEY)
    storage_service = StorageService()
    handlers = BotHandlers(ai_service, storage_service)

    # Build application with JobQueue enabled
    application = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("ask", handlers.ask_command))
    application.add_handler(CommandHandler("search", handlers.search_command))
    application.add_handler(CommandHandler("summary", handlers.summary_command))
    application.add_handler(CommandHandler("daily", handlers.summary_command))

    # Register message handler
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.message_handler)
    )

    # Schedule daily summary at 23:00 (11 PM) every day
    job_queue = application.job_queue
    if job_queue:
        # Schedule job to run daily at 23:00
        job_queue.run_daily(
            handlers.daily_summary_job,
            time=time(hour=23, minute=0),
            name="daily_summary"
        )
        logger.info("Scheduled daily summary job for 23:00 every day")
    else:
        logger.warning("JobQueue not available - daily summaries will not run automatically")

    logger.info("Bot starting…")
    application.run_polling()


if __name__ == "__main__":
    main()
