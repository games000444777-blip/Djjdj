# meta developer: @tordkor

from .. import loader, utils
import asyncio

@loader.tds
class MineEvoAutoMod(loader.Module):
    """Автосбор шахт для @mineEvo бота"""
    
    strings = {
        "name": "MineEvoAuto",
        "started": "✅ Автосбор mineEvo запущен",
        "stopped": "❌ Автосбор mineEvo остановлен",
        "collected": "💎 Собрал ресурсы!",
        "restarted": "🔄 Запустил добычу заново!"
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
        """Слушает сообщения от mineEvo"""
        
        # Ищем чат с mineEvo
        chat_id = None
        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            username = getattr(entity, 'username', None)
            if username and username.lower() == "mineevo":
                chat_id = dialog.id
                break
        
        if not chat_id:
            print("❌ Чат с @mineEvo не найден")
            return
        
        # Получаем последнее сообщение
        last_msg_id = 0
        async for message in self.client.iter_messages(chat_id, limit=1):
            last_msg_id = message.id
        
        print(f"✅ Слежу за чатом mineEvo (id: {chat_id})")
        
        while self.running:
            await asyncio.sleep(2)
            
            try:
                async for msg in self.client.iter_messages(chat_id, min_id=last_msg_id, limit=10):
                    last_msg_id = msg.id
                    text = msg.text or ""
                    
                    if "копание завершено" in text.lower() or "собери ресурсы" in text.lower():
                        if msg.reply_markup:
                            collected = False
                            restarted = False
                            
                            for row in msg.reply_markup.rows:
                                for button in row.buttons:
                                    callback_data = getattr(button, 'data', b'').decode('utf-8')
                                    
                                    # Собираем ресурсы
                                    if "mine_collect" in callback_data and not collected:
                                        await msg.click(data=callback_data)
                                        print(self.strings["collected"])
                                        collected = True
                                        await asyncio.sleep(1.5)
                                    
                                    # Запускаем добычу заново
                                    if "mine_start" in callback_data and collected and not restarted:
                                        await msg.click(data=callback_data)
                                        print(self.strings["restarted"])
                                        restarted = True
                                        await asyncio.sleep(2)
                                        break
                                
                                if restarted:
                                    break
            except Exception as e:
                print(f"Ошибка: {e}")
                await asyncio.sleep(5)
