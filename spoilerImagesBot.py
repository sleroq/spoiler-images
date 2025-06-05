import logging
import asyncio
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CallbackContext
from telegram import Update, InputMediaAnimation, InputMediaVideo, InputMediaPhoto

logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
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
        elif message.video:
          await context.bot.send_video(chat_id=chat_id, video=message.video, has_spoiler=True)
        elif message.animation:
          await context.bot.send_animation(chat_id=chat_id, animation=message.animation.file_id, has_spoiler=True)

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

if __name__ == '__main__':
  application = ApplicationBuilder().token(BOT_TOKEN).build()
  
  # Handler for media (photos, videos, animations)
  media_handler = MessageHandler(filters.ANIMATION | filters.PHOTO | filters.VIDEO, media)
  application.add_handler(media_handler)
  
  # Handler for text messages
  text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, text_message)
  application.add_handler(text_handler)
  
  application.run_polling()