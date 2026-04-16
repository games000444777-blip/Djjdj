# meta developer: @tord_kor

from .. import loader, utils
from telethon import events
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class MineEvoAutoMod(loader.Module):
    """Автосбор шахт для @mineEvo бота"""
    
    strings = {
        "name": "MineEvoAuto",
        "started": "✅ Автосбор mineEvo запущен",
        "stopped": "❌ Автосбор mineEvo остановлен"
    }
    
    def __init__(self):
        self.running = False
        self.handlers = []
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    @loader.command()
    async def mstart(self, message):
        """Запустить автосбор шахт"""
        if self.running:
            await utils.answer(message, "⚠️ Уже запущен!")
            return
        
        self.running = True
        await utils.answer(message, self.strings["started"])
        asyncio.ensure_future(self._watch_mineevo())
    
    @loader.command()
    async def mstop(self, message):
        """Остановить автосбор шахт"""
        self.running = False
        for handler in self.handlers:
            self.client.remove_event_handler(handler)
        self.handlers = []
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        try:
            entity = await self.client.get_entity("@mineevo")
            chat_id = entity.id
            
            logger.info(f"✅ Слежу за @mineevo (ID: {chat_id})")
            
            async def process(event):
                if not self.running:
                    return
                
                msg = event.message
                text = msg.raw_text or msg.text or ""
                
                if "копание завершено" in text.lower() or "собери ресурсы" in text.lower() or "ресурсы собраны" in text.lower():
                    if msg.reply_markup:
                        for row in msg.reply_markup.rows:
                            for button in row.buttons:
                                callback_data = getattr(button, 'data', b'').decode('utf-8')
                                
                                if "mine_collect" in callback_data:
                                    await msg.click(data=callback_data)
                                    await asyncio.sleep(2)
                                
                                if "mine_start" in callback_data:
                                    await msg.click(data=callback_data)
                                    await asyncio.sleep(2)
            
            h1 = self.client.add_event_handler(process, events.NewMessage(chats=chat_id))
            h2 = self.client.add_event_handler(process, events.MessageEdited(chats=chat_id))
            self.handlers = [h1, h2]
        
        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
