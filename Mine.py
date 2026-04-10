# meta developer: @tord_kor

from .. import loader, utils
from telethon import events
import requests
import json
from datetime import datetime, timedelta
import asyncio
import logging
import random
import string

logger = logging.getLogger(__name__)

GIST_ID = "bce1d6463212b4a70bcca4adf28ce517"
TOKEN = "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"
OWNER_ID = 5201054382  # ← ТЫ — ВЛАДЕЛЕЦ

def get_keys_data():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {TOKEN}"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            content = r.json()["files"]["keys.json"]["content"]
            return json.loads(content)
    except Exception as e:
        logger.error(f"Ошибка загрузки ключей: {e}")
    return {"owner_id": OWNER_ID, "keys": {}}

def update_keys_data(data):
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {TOKEN}"}
        payload = {
            "files": {
                "keys.json": {
                    "content": json.dumps(data, indent=2)
                }
            }
        }
        requests.patch(url, headers=headers, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Ошибка обновления ключей: {e}")

@loader.tds
class MineEvoAutoMod(loader.Module):
    strings = {
        "name": "MineEvoAuto",
        "started": "Автосбор запущен",
        "stopped": "Автосбор остановлен",
        "key_active": "Ключ активен до {}",
        "key_expired": "Ключ истёк",
        "key_invalid": "Ключ не найден или уже активирован",
        "key_added": "Ключ активирован до {}",
        "owner_only": "Только владелец может использовать эту команду"
    }
    
    def __init__(self):
        self.running = False
        self.handlers = []
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    def is_owner(self, user_id):
        return user_id == OWNER_ID
    
    def generate_key(self, days=30):
        chars = string.ascii_uppercase + string.digits
        key = "TORDKOR-" + ''.join(random.choice(chars) for _ in range(4)) + "-" + ''.join(random.choice(chars) for _ in range(4))
        return key
    
    @loader.command()
    async def genkey(self, message):
        user_id = (await message.get_sender()).id
        if not self.is_owner(user_id):
            await utils.answer(message, self.strings["owner_only"])
            return
        
        args = utils.get_args_raw(message)
        days = int(args) if args and args.isdigit() else 30
        
        key = self.generate_key()
        expires = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        data = get_keys_data()
        data["keys"][key] = {
            "user_id": None,
            "expires": expires,
            "created": datetime.now().strftime("%Y-%m-%d")
        }
        update_keys_data(data)
        
        await utils.answer(message, f"Новый ключ:\n`{key}`\nДействует до: {expires}")

    @loader.command()
    async def addkey(self, message):
        user_id = (await message.get_sender()).id
        key = utils.get_args_raw(message).strip()
        
        if not key:
            await utils.answer(message, "Укажи ключ: .addkey TORDKOR-XXXX-XXXX")
            return
        
        data = get_keys_data()
        if not data or key not in data["keys"]:
            await utils.answer(message, self.strings["key_invalid"])
            return
        
        key_data = data["keys"][key]
        
        if key_data["user_id"] is not None:
            await utils.answer(message, self.strings["key_invalid"])
            return
        
        if datetime.now().strftime("%Y-%m-%d") > key_data["expires"]:
            await utils.answer(message, self.strings["key_expired"])
            return
        
        key_data["user_id"] = user_id
        update_keys_data(data)
        
        await utils.answer(message, self.strings["key_added"].format(key_data["expires"]))
    
    @loader.command()
    async def checkkey(self, message):
        user_id = (await message.get_sender()).id
        
        if self.is_owner(user_id):
            await utils.answer(message, "Ты владелец — доступ без ключа")
            return
        
        data = get_keys_data()
        if not data:
            await utils.answer(message, "Ошибка сервера")
            return
        
        for key, info in data["keys"].items():
            if info["user_id"] == user_id:
                if datetime.now().strftime("%Y-%m-%d") > info["expires"]:
                    await utils.answer(message, self.strings["key_expired"])
                else:
                    await utils.answer(message, self.strings["key_active"].format(info["expires"]))
                return
        
        await utils.answer(message, "У вас нет активного ключа")

    @loader.command()
    async def start(self, message):
        user_id = (await message.get_sender()).id
        
        if self.is_owner(user_id):
            pass
        else:
            data = get_keys_data()
            valid = False
            if data:
                for key, info in data["keys"].items():
                    if info["user_id"] == user_id and datetime.now().strftime("%Y-%m-%d") <= info["expires"]:
                        valid = True
                        break
            if not valid:
                await utils.answer(message, "Нет активного ключа. Пишите @tord_kor")
                return
        
        if self.running:
            await utils.answer(message, "Уже запущен!")
            return
        
        self.running = True
        await utils.answer(message, self.strings["started"])
        
        asyncio.ensure_future(self._watch_mineevo())
    
    @loader.command()
    async def stop(self, message):
        self.running = False
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        try:
            entity = await self.client.get_entity("@mineevo")
            chat_id = entity.id
            
            logger.info(f"Слежу за @mineevo (ID: {chat_id})")
            
            async def process(event):
                if not self.running:
                    return
                
                msg = event.message
                text = msg.text or ""
                
                if "копание завершено" in text.lower() or "собери ресурсы" in text.lower() or "ресурсы собраны" in text.lower():
                    logger.info(f"Обнаружено сообщение о сборе: {text[:80]}")
                    
                    if msg.reply_markup:
                        for row in msg.reply_markup.rows:
                            for button in row.buttons:
                                callback_data = getattr(button, 'data', b'').decode('utf-8')
                                
                                if "mine_collect" in callback_data:
                                    logger.info(f"Собираю ресурсы: {callback_data}")
                                    await msg.click(data=callback_data)
                                    await asyncio.sleep(2)
                                
                                if "mine_start" in callback_data:
                                    logger.info(f"Перезапускаю шахту: {callback_data}")
                                    await msg.click(data=callback_data)
                                    await asyncio.sleep(2)
            
            self.handlers.append(self.client.add_event_handler(process, events.NewMessage(chats=chat_id)))
            self.handlers.append(self.client.add_event_handler(process, events.MessageEdited(chats=chat_id)))
        
        except Exception as e:
            logger.error(f"Ошибка запуска слежки: {e}")
