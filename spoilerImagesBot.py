import logging
import asyncio
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CallbackContext, CommandHandler
from telegram import Update, InputMediaAnimation, InputMediaVideo, InputMediaPhoto

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
)

# Suppress verbose httpx logs
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram.ext').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

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
            "<b>Анонимный бот пересылки сообщений</b>\n\n"
            "<b>Как работает:</b>\n"
            "• Отправляешь сообщение (текст, фото, видео)\n"
            "• Бот пересылает его в чат как спойлер\n"
            "• Никто не узнает кто отправил\n\n"
            "<b>Что нужно знать:</b>\n"
            "• Ответить через бота нельзя\n"
            "• Работает только в личке\n\n"
            "Команды: /help"
        )
        await update.message.reply_text(welcome_message, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    if update.effective_chat.type == 'private':
        help_message = (
            "<b>Справка</b>\n\n"
            "<b>Что можно отправлять:</b>\n"
            "• Текст\n"
            "• Фото\n"
            "• Видео\n"
            "• Гифки\n"
            "• Группы файлов\n\n"
            "<b>Как работает:</b>\n"
            "• Всё отправляется как спойлер\n"
            "• Анонимно\n"
            "• Ответить нельзя\n"
            "• Только в личке\n\n"
            "<b>Команды:</b>\n"
            "/start - описание\n"
            "/help - эта справка\n\n"
            "Просто отправь сообщение."
        )
        await update.message.reply_text(help_message, parse_mode='HTML')

async def echo_media_group(context: CallbackContext, media_group_id):
  response = []
  original_message = media_groups[media_group_id][0]  # Get the first message from the group
  user = original_message.from_user
  
  # Log user info for media group forwarding
  logger.info(f"Forwarding media group from user - ID: {user.id}, Username: {user.username}, "
              f"First Name: {user.first_name}, Last Name: {user.last_name}, "
              f"Media Group ID: {media_group_id}, Items: {len(media_groups[media_group_id])}")
  
  for message in media_groups[media_group_id]:
    if message.photo:
      response.append(InputMediaPhoto(media=message.photo[-1].file_id, has_spoiler=True))
    elif message.video:
      response.append(InputMediaVideo(media=message.video.file_id, has_spoiler=True))
    elif message.animation:   # Check if the media is an animation/GIF file.
      response.append(InputMediaAnimation(media=message.animation.file_id, has_spoiler=True))
  await context.bot.send_media_group(chat_id=chat_id, media=response)
  
  # Reply to the user to confirm delivery
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
        user = message.from_user
        if message.photo:
          logger.info(f"Forwarding photo from user - ID: {user.id}, Username: {user.username}, "
                      f"First Name: {user.first_name}, Last Name: {user.last_name}")
          await context.bot.send_photo(chat_id=chat_id, photo=message.photo[-1], has_spoiler=True)
          await message.reply_text("переслал")
        elif message.video:
          logger.info(f"Forwarding video from user - ID: {user.id}, Username: {user.username}, "
                      f"First Name: {user.first_name}, Last Name: {user.last_name}")
          await context.bot.send_video(chat_id=chat_id, video=message.video, has_spoiler=True)
          await message.reply_text("переслал")
        elif message.animation:
          logger.info(f"Forwarding animation from user - ID: {user.id}, Username: {user.username}, "
                      f"First Name: {user.first_name}, Last Name: {user.last_name}")
          await context.bot.send_animation(chat_id=chat_id, animation=message.animation.file_id, has_spoiler=True)
          await message.reply_text("переслал")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message is not None and update.effective_chat.type == 'private':
    message = update.message
    if message.text:
      user = message.from_user
      # Log user info for text message forwarding
      logger.info(f"Forwarding text message from user - ID: {user.id}, Username: {user.username}, "
                  f"First Name: {user.first_name}, Last Name: {user.last_name}, "
                  f"Message length: {len(message.text)} chars")
      
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