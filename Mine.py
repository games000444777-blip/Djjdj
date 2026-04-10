# meta developer: @tordkor

from .. import loader, utils
import asyncio

@loader.tds
class MineEvoAutoMod(loader.Module):
    """Автосбор шахт для @mineEvo бота"""
    
    strings = {
        "name": "MineEvoAuto",
        "started": "✅ Автосбор mineEvo запущен (DEBUG MODE)",
        "stopped": "❌ Автосбор mineEvo остановлен"
    }
    
    def __init__(self):
        self.running = False
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    @loader.command()
    async def start(self, message):
        """Запустить автосбор"""
        self.running = True
        await utils.answer(message, self.strings["started"])
        asyncio.create_task(self._watch_mineevo())
    
    @loader.command()
    async def stop(self, message):
        """Остановить автосбор"""
        self.running = False
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        """Слушает сообщения от mineEvo с DEBUG логами"""
        
        print("🔍 [DEBUG] Начинаю поиск чата с mineEvo...")
        
        # Ищем чат с mineEvo
        chat_id = None
        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            username = getattr(entity, 'username', None)
            print(f"🔍 [DEBUG] Проверяю диалог: {username or 'NoUsername'}")
            
            if username and username.lower() == "mineevo":
                chat_id = dialog.id
                print(f"✅ [DEBUG] Найден чат с mineEvo! ID: {chat_id}")
                break
        
        if not chat_id:
            print("❌ [DEBUG] Чат с @mineEvo не найден!")
            return
        
        # Получаем последнее сообщение
        last_msg_id = 0
        async for message in self.client.iter_messages(chat_id, limit=1):
            last_msg_id = message.id
            print(f"✅ [DEBUG] Последнее сообщение ID: {last_msg_id}")
        
        print(f"✅ [DEBUG] Слежу за чатом mineEvo...")
        
        while self.running:
            await asyncio.sleep(2)
            
            try:
                msg_count = 0
                async for msg in self.client.iter_messages(chat_id, min_id=last_msg_id, limit=10):
                    msg_count += 1
                    last_msg_id = msg.id
                    text = msg.text or ""
                    
                    print(f"📨 [DEBUG] Новое сообщение (ID {msg.id}): {text[:60]}...")
                    
                    if "копание завершено" in text.lower() or "собери ресурсы" in text.lower():
                        print("🎯 [DEBUG] Обнаружено сообщение о сборе!")
                        
                        if msg.reply_markup:
                            print(f"🔘 [DEBUG] Кнопок найдено: {len(msg.reply_markup.rows)}")
                            
                            for row_idx, row in enumerate(msg.reply_markup.rows):
                                for btn_idx, button in enumerate(row.buttons):
                                    callback_data = getattr(button, 'data', b'').decode('utf-8')
                                    button_text = getattr(button, 'text', 'NoText')
                                    
                                    print(f"🔘 [DEBUG] Кнопка [{row_idx}][{btn_idx}]: '{button_text}' | data: {callback_data}")
                                    
                                    # Собираем ресурсы
                                    if "mine_collect" in callback_data:
                                        print(f"💎 [DEBUG] Нажимаю 'Собрать' (data: {callback_data})")
                                        await msg.click(data=callback_data)
                                        await asyncio.sleep(2)
                                    
                                    # Запускаем добычу заново
                                    if "mine_start" in callback_data:
                                        print(f"🔄 [DEBUG] Нажимаю 'Начать заново' (data: {callback_data})")
                                        await msg.click(data=callback_data)
                                        await asyncio.sleep(2)
                        else:
                            print("❌ [DEBUG] У сообщения нет кнопок!")
                
                if msg_count > 0:
                    print(f"📬 [DEBUG] Обработано сообщений: {msg_count}")
                    
            except Exception as e:
                print(f"❌ [DEBUG] Ошибка: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
