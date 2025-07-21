import asyncio
from aiogram import Bot, types
from my_package import log, dp, bot

async def main(mybot) -> None:
    
    # Set bot command menu
    await mybot.set_my_commands([
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="newchat", description="Start a new chat session"),
    ])
    log.info('starting bot')
    await dp.start_polling(mybot)

if __name__ == "__main__":   

    asyncio.run(main(bot))