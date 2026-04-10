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
        "stopped": "❌ Автосбор mineEvo остановлен"
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
    
    @loader.command()
    async def stop(self, message):
        """Остановить автосбор"""
        self.running = False
        if self.task:
            self.task.cancel()
        await utils.answer(message, self.strings["stopped"])
    
    async def _watch_mineevo(self):
        try:
            logger.info("🔍 Ищу @mineevo...")
            
            entity = await self.client.get_entity("@mineevo")
            chat_id = entity.id
            logger.info(f"✅ Найден! ID: {chat_id}")
            
            # Сразу проверяем последние 10 сообщений (на случай, если уже есть "Копание завершено")
            logger.info("🔍 Проверяю последние сообщения...")
            await self._check_messages(chat_id, limit=10)
            
            # Запоминаем ID последнего сообщения
            last_msg_id = 0
            async for msg in self.client.iter_messages(chat_id, limit=1):
                last_msg_id = msg.id
            
            logger.info(f"✅ Слежу. Последнее сообщение: {last_msg_id}")
            
            # Основной цикл
            while self.running:
                await asyncio.sleep(3)
                
                try:
                    # Проверяем только НОВЫЕ сообщения
                    await self._check_messages(chat_id, min_id=last_msg_id, limit=10)
                    
                    # Обновляем last_msg_id
                    async for msg in self.client.iter_messages(chat_id, limit=1):
                        last_msg_id = msg.id
                        break
                
                except Exception as e:
                    logger.error(f"Ошибка: {e}")
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    async def _check_messages(self, chat_id, min_id=0, limit=10):
        """Проверяет сообщения и жмёт кнопки"""
        async for msg in self.client.iter_messages(chat_id, min_id=min_id, limit=limit):
            text = msg.text or ""
            
            logger.info(f"📨 [{msg.id}] {text[:100]}")
            
            if msg.reply_markup:
                for row in msg.reply_markup.rows:
                    for button in row.buttons:
                        callback_data = getattr(button, 'data', b'').decode('utf-8')
                        button_text = getattr(button, 'text', '')
                        
                        logger.info(f"🔘 '{button_text}' -> {callback_data}")
                        
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
