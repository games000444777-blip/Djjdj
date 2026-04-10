# meta developer: @tordkor

from .. import loader, utils
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class MineEvoAutoMod(loader.Module):
    """Автосбор шахт для @mineEvo бота"""
    
    strings = {
        "name": "MineEvoAuto",
        "started": "✅ Автосбор mineEvo запущен",
        "stopped": "❌ Автосбор mineEvo остановлен",
        "working": "⚙️ Модуль работает..."
    }
    
    def __init__(self):
        self.running = False
        self.task = None
    
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
        
        self.task = asyncio.ensure_future(self._watch_mineevo())
        
        logger.info("MineEvoAuto: Модуль запущен!")
        await message.respond(self.strings["working"])
    
    @loader.command()
    async def stop(self, message):
        """Остановить автосбор"""
        self.running = False
        if self.task:
            self.task.cancel()
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        """Слушает сообщения от mineEvo"""
        
        try:
            logger.info("🔍 Ищу чат с mineEvo...")
            
            # Ищем чат с mineEvo
            chat_id = None
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                username = getattr(entity, 'username', None)
                
                if username and username.lower() == "mineevo":
                    chat_id = dialog.id
                    logger.info(f"✅ Найден чат mineEvo: {chat_id}")
                    break
            
            if not chat_id:
                logger.error("❌ Чат с @mineEvo не найден!")
                return
            
            # Получаем последнее сообщение
            last_msg_id = 0
            async for msg in self.client.iter_messages(chat_id, limit=1):
                last_msg_id = msg.id
            
            logger.info(f"✅ Начинаю слежку. Последнее сообщение: {last_msg_id}")
            
            while self.running:
                await asyncio.sleep(3)
                
                try:
                    async for msg in self.client.iter_messages(chat_id, min_id=last_msg_id, limit=5):
                        last_msg_id = msg.id
                        text = msg.text or ""
                        text_lower = text.lower()
                        
                        logger.info(f"📨 Новое сообщение: {text[:80]}")
                        
                        # Проверяем все варианты написания
                        if any(keyword in text_lower for keyword in [
                            "копание завершено",
                            "собери ресурсы",
                            "завершено"
                        ]):
                            logger.info("🎯 ОБНАРУЖЕН СБОР!")
                            
                            if msg.reply_markup:
                                logger.info(f"🔘 Кнопок: {len(msg.reply_markup.rows)}")
                                
                                for row in msg.reply_markup.rows:
                                    for button in row.buttons:
                                        callback_data = getattr(button, 'data', b'').decode('utf-8')
                                        button_text = getattr(button, 'text', '')
                                        
                                        logger.info(f"🔘 Кнопка: '{button_text}' | {callback_data}")
                                        
                                        # Собираем
                                        if "mine_collect" in callback_data:
                                            logger.info(f"💎 СОБИРАЮ!")
                                            await msg.click(data=callback_data)
                                            await asyncio.sleep(2)
                                        
                                        # Перезапускаем
                                        if "mine_start" in callback_data:
                                            logger.info(f"🔄 ПЕРЕЗАПУСКАЮ!")
                                            await msg.click(data=callback_data)
                                            await asyncio.sleep(2)
                            else:
                                logger.warning("❌ Кнопок нет!")
                
                except Exception as e:
                    logger.error(f"Ошибка в цикле: {e}")
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
