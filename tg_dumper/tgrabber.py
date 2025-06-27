#!/usr/bin/env python3
import os
import json
import telethon.sessions
from datetime import datetime
from telethon import TelegramClient

from configs.project_paths import tg_dump_media_path, tg_dump_last_dump_path, tg_dump_text_path, DATA_PATH
from tg_dumper.chatdata import Message

from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.types import (
    MessageService, DocumentAttributeVideo, DocumentAttributeAudio,
    DocumentAttributeFilename, DocumentAttributeSticker, Channel, User
)

from configs.telegram_config import API_ID, API_HASH, SESSION_STRING, group_username, specific_topic_id

downloaded_avatars = {}


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat(sep=' ').replace('+00:00', '')
    raise TypeError(f"[ERROR] Ошибка сериализации {type(obj)}")


def make_user_string(peer):
    if not peer:
        return None

    username = getattr(peer, 'username', '')
    title = ''
    if isinstance(peer, User):
        title = ' '.join(filter(None, [peer.first_name, peer.last_name]))
    elif isinstance(peer, Channel):
        title = peer.title
    else:
        raise Exception(f'[ERROR] Неизвестный пир: {peer}')

    return f"@{username} ({title})" if username else title or f"id:{peer.id}"


def get_attr(document, attr_type):
    return next((a for a in document.attributes if isinstance(a, attr_type)), None)


def get_file_name(document):
    attr = get_attr(document, DocumentAttributeFilename)
    return attr.file_name if attr else 'unknown'


def get_duration(document):
    attr = get_attr(document, DocumentAttributeVideo) or get_attr(document, DocumentAttributeAudio)
    return getattr(attr, 'duration', 'unknown')


async def save_media(client, message, folder=tg_dump_media_path):
    os.makedirs(folder, exist_ok=True)
    if not message.media:
        return None
    try:
        path = await client.download_media(message.media, file=folder)
        return path
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки сообщения с id - {message.id}: {e}")
        return None


async def download_user_avatar(client, user, folder):
    if not user or not isinstance(user, User):
        return None

    user_id = user.id
    if user_id in downloaded_avatars:
        return downloaded_avatars[user_id]

    os.makedirs(folder, exist_ok=True)
    try:
        path = await client.download_profile_photo(user, file=os.path.join(folder, f"{user_id}.jpg"))
        downloaded_avatars[user_id] = path
        return path
    except Exception as e:
        print(f"[WARNING] Не удалось загрузить аватар для user_id={user_id}: {e}")
        return None


async def extract_message_data(message, client):
    reply_to_id = None
    topic_id = None
    media_info = {}

    if message.reply_to:
        r = message.reply_to
        if r.forum_topic:
            topic_id = r.reply_to_top_id or r.reply_to_msg_id
            reply_to_id = r.reply_to_msg_id
        else:
            reply_to_id = r.reply_to_msg_id

    topic_id = int(topic_id or 1)
    if topic_id != specific_topic_id:
        return None, None

    original_text = message.text or ""

    if message.media:
        path = await save_media(client, message)
        media_type = message.media.__class__.__name__.lower()

        if type(path) == str:
            if path.startswith(DATA_PATH):
                path = path.replace(DATA_PATH + "/", '', 1)

        media_info = {
            'type': media_type,
            'path': path,
        }

        document = getattr(message, 'document', None)
        if document:
            file_name = get_file_name(document)
            duration = get_duration(document)
            media_info.update({
                'file_name': file_name,
                'duration': duration,
                'mime_type': getattr(document, 'mime_type', 'unknown'),
                'size': getattr(document, 'size', None),
            })

        if 'photo' in media_type:
            caption = f"[ФОТО сохранено по адресу {path}]"
        elif 'video' in media_type:
            caption = f"[ВИДЕО сохранено по адресу {path}]"
        elif 'audio' in media_type:
            caption = f"[АУДИО сохранено по адресу {path}]"
        elif 'voice' in media_type:
            caption = f"[ГОЛОСОВОЕ сохранено по адресу {path}]"
        elif 'sticker' in media_type:
            caption = f"[СТИКЕР сохранен по адресу {path}]"
        else:
            caption = f"[{media_type.upper()} saved to {path}]"

        if original_text:
            text = f"{original_text}\n\n{caption}"
        else:
            text = caption
    else:
        sender = await message.get_sender()
        avatar_path = await download_user_avatar(client, sender, tg_dump_media_path)
        if avatar_path:
            media_info = {
                'type': 'profile_photo',
                'path': avatar_path,
            }
        text = original_text

    sender = await message.get_sender()
    fwd_sender = None
    fwd_date = None
    if message.fwd_from:
        fwd_date = message.fwd_from.date
        fwd_sender = message.fwd_from.from_name or None
        if not fwd_sender and message.fwd_from.from_id:
            try:
                ent = await client.get_entity(message.fwd_from.from_id)
                fwd_sender = make_user_string(ent)
            except Exception:
                fwd_sender = None

    msg = Message(
        message.id, message.date, text,
        make_user_string(sender),
        fwd_date, fwd_sender, reply_to_id
    )

    return topic_id, {'downloaded_text': msg, 'downloaded_media': media_info or None}


def load_last_dump_date(filename=os.path.join(tg_dump_last_dump_path, "last_dump_date.txt")):
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            date_str = f.read().strip()
            if date_str:
                return datetime.fromisoformat(date_str)
    except Exception as e:
        print(f"[WARNING] Невозможно прочитать дату последнего дампа!: {e}")
    return None


def save_last_dump_date(date, filename=os.path.join(tg_dump_last_dump_path, "last_dump_date.txt")):
    try:
        os.makedirs(tg_dump_last_dump_path, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(date.isoformat())
    except Exception as e:
        print(f"[WARNING] Невозможно сохранить дату последнего дампа!: {e}")


async def grabber():
    session = telethon.sessions.StringSession(SESSION_STRING)
    client = TelegramClient(session, API_ID, API_HASH)
    await client.start()
    print("Запущен дамп телеграм топика!")

    group = await client.get_entity(group_username)
    print(f"Группа: {group.title}")

    topics_resp = await client(GetForumTopicsRequest(
        channel=group, offset_date=0, offset_id=0, offset_topic=0, limit=100
    ))
    topic_ids = {t.id for t in topics_resp.topics}
    topic_messages = {}
    topics = [(t.id, t.title) for t in topics_resp.topics]

    last_dump_date = load_last_dump_date()
    print(f"Дата последнего дампа: {last_dump_date}")

    newest_date = last_dump_date

    async for message in client.iter_messages(group, reverse=True):
        if isinstance(message, MessageService):
            continue

        if last_dump_date:
            if message.date <= last_dump_date and not message.edit_date:
                continue

        topic_id, entry = await extract_message_data(message, client)
        if not entry:
            continue

        topic_messages.setdefault(topic_id, []).append(entry)

        if newest_date is None or message.date > newest_date:
            newest_date = message.date

        print('[PROCESSING DUMP] wait\n', end='', flush=True)

    print("\nСтатистика топика:")
    for tid, msgs in topic_messages.items():
        print(f"В топике - {tid}: {len(msgs)} сообщений(-я)")

    os.makedirs(tg_dump_text_path, exist_ok=True)

    with open(os.path.join(tg_dump_text_path, "non_filtered_cv.json"), "w", encoding="utf-8") as f:
        json.dump({"text": topic_messages},
                  f, ensure_ascii=False, indent=4, default=json_serial)

    if newest_date:
        save_last_dump_date(newest_date)

    await client.disconnect()
