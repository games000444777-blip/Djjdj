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
            
            try:
                entity = await self.client.get_entity("@mineevo")
                chat_id = entity.id
                logger.info(f"✅ Найден бот mineEvo! ID: {chat_id}")
            except Exception as e:
                logger.error(f"❌ Не удалось найти @mineevo: {e}")
                return
            
            last_msg_id = 0
            async for msg in self.client.iter_messages(chat_id, limit=1):
                last_msg_id = msg.id
            
            logger.info(f"✅ Слежу за чатом. Последнее сообщение: {last_msg_id}")
            
            while self.running:
                await asyncio.sleep(3)
                
                try:
                    async for msg in self.client.iter_messages(chat_id, min_id=last_msg_id, limit=10):
                        last_msg_id = msg.id
                        text = msg.text or ""
                        text_lower = text.lower()
                        
                        logger.info(f"📨 [{msg.id}] {text[:100]}")
                        
                        # Если это сообщение о завершении копания
                        if any(kw in text_lower for kw in ["копание завершено", "собери ресурсы"]):
                            logger.info("🎯 ОБНАРУЖЕН СБОР!")
                            
                            if msg.reply_markup:
                                for row in msg.reply_markup.rows:
                                    for button in row.buttons:
                                        callback_data = getattr(button, 'data', b'').decode('utf-8')
                                        button_text = getattr(button, 'text', '')
                                        
                                        logger.info(f"🔘 '{button_text}' | {callback_data}")
                                        
                                        if "mine_collect" in callback_data:
                                            logger.info(f"💎 СОБИРАЮ РЕСУРСЫ!")
                                            await msg.click(data=callback_data)
                                            
                                            # Ждём, пока бот пришлёт новое сообщение с кнопкой перезапуска
                                            await asyncio.sleep(3)
                                            
                                            # Ищем новое сообщение с кнопкой mine_start
                                            logger.info("🔍 Ищу кнопку перезапуска...")
                                            async for new_msg in self.client.iter_messages(chat_id, limit=5):
                                                if new_msg.reply_markup:
                                                    for r in new_msg.reply_markup.rows:
                                                        for b in r.buttons:
                                                            cd = getattr(b, 'data', b'').decode('utf-8')
                                                            bt = getattr(b, 'text', '')
                                                            
                                                            logger.info(f"🔘 Новая кнопка: '{bt}' | {cd}")
                                                            
                                                            if "mine_start" in cd:
                                                                logger.info(f"🔄 ПЕРЕЗАПУСКАЮ ШАХТУ!")
                                                                await new_msg.click(data=cd)
                                                                await asyncio.sleep(2)
                                                                break
                                            
                                            break
                        
                        # Если это сообщение "Ресурсы собраны" (на всякий случай)
                        if "ресурсы собраны" in text_lower:
                            logger.info("🎯 ОБНАРУЖЕНО СООБЩЕНИЕ О СБОРЕ!")
                            
                            if msg.reply_markup:
                                for row in msg.reply_markup.rows:
                                    for button in row.buttons:
                                        callback_data = getattr(button, 'data', b'').decode('utf-8')
                                        button_text = getattr(button, 'text', '')
                                        
                                        logger.info(f"🔘 '{button_text}' | {callback_data}")
                                        
                                        if "mine_start" in callback_data:
                                            logger.info(f"🔄 ПЕРЕЗАПУСКАЮ ШАХТУ!")
                                            await msg.click(data=callback_data)
                                            await asyncio.sleep(2)
                
                except Exception as e:
                    logger.error(f"Ошибка в цикле: {e}")
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
