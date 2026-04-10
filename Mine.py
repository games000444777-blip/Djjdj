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
        self.handler_new = None
        self.handler_edit = None
    
    async def client_ready(self, client, db):
        self.client = client
        self.db = db
    
    @loader.command()
    async def start(self, message):
        """Запустить автосбор"""
        if self.running:
            await utils.answer(message, "⚠️ Уже запущен!")
            return
        
        self.running = True
        await utils.answer(message, self.strings["started"])
        
        try:
            entity = await self.client.get_entity("@mineevo")
            chat_id = entity.id
            
            logger.info(f"✅ Найден @mineevo, ID: {chat_id}")
            
            # Функция обработки сообщения (одна для всех)
            async def process_message(event):
                if not self.running:
                    return
                
                text = event.message.text or ""
                msg_type = "✏️ EDIT" if hasattr(event, 'message') and event.message.edit_date else "📨 NEW"
                
                logger.info(f"{msg_type}: {text[:100]}")
                
                if event.message.reply_markup:
                    for row in event.message.reply_markup.rows:
                        for button in row.buttons:
                            callback_data = getattr(button, 'data', b'').decode('utf-8')
                            button_text = getattr(button, 'text', '')
                            
                            logger.info(f"🔘 '{button_text}' -> {callback_data}")
                            
                            # Собираем
                            if "mine_collect" in callback_data:
                                logger.info(f"💎 СОБИРАЮ!")
                                await event.message.click(data=callback_data)
                                await asyncio.sleep(2)
                            
                            # Перезапускаем
                            if "mine_start" in callback_data:
                                logger.info(f"🔄 ПЕРЕЗАПУСКАЮ!")
                                await event.message.click(data=callback_data)
                                await asyncio.sleep(2)
            
            # Обработчик НОВЫХ сообщений
            @self.client.on(events.NewMessage(chats=chat_id))
            async def handler_new(event):
                await process_message(event)
            
            # Обработчик РЕДАКТИРОВАНИЯ сообщений
            @self.client.on(events.MessageEdited(chats=chat_id))
            async def handler_edit(event):
                await process_message(event)
            
            self.handler_new = handler_new
            self.handler_edit = handler_edit
            
            logger.info("✅ Слушаю НОВЫЕ и РЕДАКТИРУЕМЫЕ сообщения от @mineevo")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске: {e}")
            import traceback
            traceback.print_exc()
    
    @loader.command()
    async def stop(self, message):
        """Остановить автосбор"""
        self.running = False
        
        # Удаляем обработчики
        if self.handler_new:
            self.client.remove_event_handler(self.handler_new)
            self.handler_new = None
        
        if self.handler_edit:
            self.client.remove_event_handler(self.handler_edit)
            self.handler_edit = None
        
        await utils.answer(message, self.strings["stopped"])
