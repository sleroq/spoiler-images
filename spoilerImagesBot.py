import logging
import asyncio
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CallbackContext, CommandHandler
from telegram import Update, InputMediaAnimation, InputMediaVideo, InputMediaPhoto

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.WARNING
)

# Load configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")
if not CHAT_ID:
    raise ValueError("CHAT_ID environment variable is required")

try:
    chat_id = int(CHAT_ID)
except ValueError:
    raise ValueError("CHAT_ID must be a valid integer")

media_groups = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    if update.effective_chat.type == 'private':
        welcome_message = (
            "🤖 *Добро пожаловать в анонимный бот пересылки сообщений!*\n\n"
            "📝 *Как это работает:*\n"
            "• Отправьте мне любое сообщение (текст, фото, видео, анимации)\n"
            "• Я перешлю его в групповой чат как спойлер\n"
            "• Все сообщения анонимны - никто не узнает, кто их отправил\n\n"
            "⚠️ *Важно знать:*\n"
            "• Ответы из группового чата невозможны через бота\n"
            "• Ваша личность полностью анонимна\n"
            "• Бот работает только в личных сообщениях\n\n"
            "💡 Используйте /help для получения дополнительной информации"
        )
        await update.message.reply_text(welcome_message, parse_mode='MarkdownV2')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    if update.effective_chat.type == 'private':
        help_message = (
            "ℹ️ *Справка по боту*\n\n"
            "*Поддерживаемые типы сообщений:*\n"
            "• 📝 Текстовые сообщения\n"
            "• 📷 Фотографии\n"
            "• 🎥 Видео\n"
            "• 🎭 Анимации/GIF\n"
            "• 📎 Группы медиафайлов\n\n"
            "*Особенности:*\n"
            "• Все сообщения отправляются как спойлеры\n"
            "• Полная анонимность отправителя\n"
            "• Нет возможности получить ответ\n"
            "• Работает только в личных сообщениях\n\n"
            "*Команды:*\n"
            "/start \\- показать приветствие\n"
            "/help \\- показать эту справку\n\n"
            "Просто отправьте сообщение, чтобы переслать его анонимно\\!"
        )
        await update.message.reply_text(help_message, parse_mode='MarkdownV2')

async def echo_media_group(context: CallbackContext, media_group_id):
  response = []
  for message in media_groups[media_group_id]:
    if message.photo:
      response.append(InputMediaPhoto(media=message.photo[-1].file_id, has_spoiler=True))
    elif message.video:
      response.append(InputMediaVideo(media=message.video.file_id, has_spoiler=True))
    elif message.animation:   # Check if the media is an animation/GIF file.
      response.append(InputMediaAnimation(media=message.animation.file_id, has_spoiler=True))
  await context.bot.send_media_group(chat_id=chat_id, media=response)
  
  # Reply to the user to confirm delivery
  original_message = media_groups[media_group_id][0]  # Get the first message from the group
  await context.bot.send_message(
    chat_id=original_message.chat_id,
    text="переслал",
    reply_to_message_id=original_message.message_id
  )
  
  del media_groups[media_group_id]

async def media(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message is not None:
    message = update.message
    media_group_id = message.media_group_id
    if update.effective_chat.type == 'private':
      if media_group_id:
        if media_group_id not in media_groups:
          media_groups[media_group_id] = [message]
          asyncio.get_event_loop().call_later(1.0, lambda: asyncio.create_task(echo_media_group(context, media_group_id)))
        else:
          media_groups[media_group_id].append(message)
      else:
        if message.photo:
          await context.bot.send_photo(chat_id=chat_id, photo=message.photo[-1], has_spoiler=True)
          await message.reply_text("переслал")
        elif message.video:
          await context.bot.send_video(chat_id=chat_id, video=message.video, has_spoiler=True)
          await message.reply_text("переслал")
        elif message.animation:
          await context.bot.send_animation(chat_id=chat_id, animation=message.animation.file_id, has_spoiler=True)
          await message.reply_text("переслал")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message is not None and update.effective_chat.type == 'private':
    message = update.message
    if message.text:
      # Wrap the text in spoiler formatting using MarkdownV2 syntax
      spoiler_text = f"||{message.text}||"
      await context.bot.send_message(
        chat_id=chat_id, 
        text=spoiler_text, 
        parse_mode='MarkdownV2'
      )
      await message.reply_text("переслал")

if __name__ == '__main__':
  application = ApplicationBuilder().token(BOT_TOKEN).build()
  
  # Command handlers
  application.add_handler(CommandHandler("start", start_command))
  application.add_handler(CommandHandler("help", help_command))
  
  # Handler for media (photos, videos, animations)
  media_handler = MessageHandler(filters.ANIMATION | filters.PHOTO | filters.VIDEO, media)
  application.add_handler(media_handler)
  
  # Handler for text messages
  text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
  application.add_handler(text_handler)
  
  application.run_polling()