from telethon import TelegramClient, events, Button
import asyncio
from google.cloud import firestore, secretmanager
import json
from datetime import datetime, timedelta
import os

# Функция для получения секрета из Google Secret Manager
def access_secret_version(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode('UTF-8')

# Используйте свой project_id Google Cloud
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')

# Извлечение секретов
api_id = access_secret_version(project_id, 'telegram_api_id')
api_hash = access_secret_version(project_id, 'telegram_api_hash')
bot_token = access_secret_version(project_id, 'telegram_bot_token')
channel_configs = json.loads(access_secret_version(project_id, 'telegram_channel_configs'))

# Инициализация Firestore
db = firestore.Client()

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Функции для работы с Firestore
def save_vote(message_id, vote, vote_weight):
    doc_ref = db.collection('votes').document(str(message_id))
    doc_ref.set({vote: firestore.Increment(vote_weight)}, merge=True)

def get_votes(message_id):
    doc_ref = db.collection('votes').document(str(message_id))
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return {'yes': 0, 'no': 0}

def start_vote(message_id):
    db.collection('votes').document(str(message_id)).set({
        'start_time': datetime.now(),
        'status': 'in_progress'
    })

def finish_vote(message_id):
    db.collection('votes').document(str(message_id)).update({
        'status': 'completed'
    })

def get_pending_votes():
    votes = db.collection('votes').where('status', '==', 'in_progress').stream()
    return {vote.id: vote.to_dict() for vote in votes}

# Измененная функция для проверки результатов голосования
async def check_vote_result(message_id, delay_hours):
    await asyncio.sleep(delay_hours * 3600)
    votes = get_votes(message_id)
    if votes['yes'] > votes['no']:
        # Логика перевода токена
        pass
    finish_vote(message_id)

# Функция для восстановления после перезапуска
async def restore_pending_votes():
    pending_votes = get_pending_votes()
    for message_id, vote_info in pending_votes.items():
        time_passed = datetime.now() - vote_info['start_time']
        remaining_time = timedelta(hours=24) - time_passed
        if remaining_time.total_seconds() > 0:
            asyncio.create_task(check_vote_result(message_id, remaining_time.total_seconds() / 3600))

# Обработчики событий Telegram
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('Привет! Отправьте видео с описанием.')

@client.on(events.NewMessage(func=lambda e: e.video))
async def handle_video(event):
    for channel in channel_configs:
        msg = await client.send_message(channel, event.message, link_preview=False, buttons=[
            [Button.inline('Да', 'yes'), Button.inline('Нет', 'no')]
        ])
        start_vote(msg.id)
        asyncio.create_task(check_vote_result(msg.id, 24))

@client.on(events.CallbackQuery)
async def callback(event):
    message_id = event.original_update.msg_id
    voter_username = await client.get_entity(event.original_update.user_id)
    vote_weight = channel_configs[event.chat.username].get('voters', {}).get(voter_username, 1)
    vote = event.data.decode('utf-8')

    save_vote(message_id, vote, vote_weight)
    await event.answer(f'Ваш голос за "{vote}" учтен с весом {vote_weight}.', alert=True)

async def main():
    await restore_pending_votes()
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
