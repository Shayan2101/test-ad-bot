from typing import Final

from telegram import (
    Update,
    InlineQueryResultPhoto,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    filters,
    MessageHandler,
    InlineQueryHandler,
)
import logging

from mongo_client import AdsMongoClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN: Final = "6899268959:AAFPG0xmG9y2qKozHVuSKqcCealf7u6mQQo"

CATEGORY, PHOTO, DESCRIPTION = range(3)
# db connection
db_client = AdsMongoClient("localhost", 27017)
# add your user ids here, you can use @userinfobot to get your user id
# DO NOT REMOVE EXISTING IDs
dev_ids = [92129627, 987654321, 198211817]


async def start_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="سلام، من ربات ثبت آگهی هستم. برای ثبت آگهی جدید از دستور /add_advertising استفاده کنید.",
        reply_to_message_id=update.effective_message.id,
    )


async def add_category_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in dev_ids:
        category = " ".join(context.args)
        db_client.add_category(category=category)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"دسته بندی {category} با موفقیت اضافه شد.",
            reply_to_message_id=update.effective_message.id,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="شما اجازه دسترسی به این دستور را ندارید.",
            reply_to_message_id=update.effective_message.id,
        )


async def add_advertising_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    categories = db_client.get_categories()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "لطفا از بین دسته بندی های زیر یکی را انتخاب کنید:\n"+"\n".join(categories),
        reply_to_message_id=update.effective_message.id,
    )
    return CATEGORY


async def choice_category_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["category"] = update.effective_message.text
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "لطفا عکس آگهی خود را ارسال کنید.",
        reply_to_message_id=update.effective_message.id,
    )
    return PHOTO


async def photo_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["photo_url"] = update.effective_message.photo[-1].file_id
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "لطفا توضیحات آگهی خود را وارد کنید. در توضیحات می توانید اطلاعاتی مانند قیمت، شماره تماس و ... را وارد کنید.",
        reply_to_message_id=update.effective_message.id,
    )
    return DESCRIPTION


async def description_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.effective_message.text
    db_client.add_advertising(
        user_id=update.effective_user.id,
        category=context.user_data["category"],
        photo_url=context.user_data["photo_url"],
        description=context.user_data["description"]
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "آگهی شما با موفقیت ثبت شد.",
        reply_to_message_id=update.effective_message.id,
    )
    return ConversationHandler.END


async def cancel_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text = "عملیات ثبت آگهی لغو شد. برای ثبت آگهی جدید از دستور /add_category استفاده کنید.",
        reply_to_message_id=update.effective_message.id,
    )
    return ConversationHandler.END


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command_handler))
    app.add_handler(CommandHandler("add_category", add_category_command_handler))
    app.add_handler(
        ConversationHandler(
            entry_points=[
                CommandHandler("add_advertising", add_advertising_command_handler)
            ],
            states={
                CATEGORY: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, choice_category_message_handler
                    )
                ],
                PHOTO: [
                    MessageHandler(filters.PHOTO, photo_message_handler),
                ],
                DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND, description_message_handler
                    )
                ],
            },
            fallbacks=[
                CommandHandler("cancel", cancel_command_handler),
            ],
            allow_reentry=True,
        )
    )
    app.run_polling()