@loader.command()
async def start(self, message):
    user_id = (await message.get_sender()).id
    print(f"ТВОЙ ID: {user_id}")  # ← это будет в логе
    
    if user_id != 14189883:
        await utils.answer(message, f"ТЫ НЕ ВЛАДЕЛЕЦ! Твой ID: {user_id}")
        return
    
    await utils.answer(message, "ТЫ ВЛАДЕЛЕЦ! Запускаю...")
    # дальше код запуска
