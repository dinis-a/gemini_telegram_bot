import asyncio

from aiogram import Bot, types

from gemini_bot import bot, dp, log, start_bot, stop_bot


async def main(mybot) -> None:

    # Set bot command menu
    await mybot.set_my_commands(
        [
            types.BotCommand(command="start", description="Start the bot"),
            types.BotCommand(command="new_chat", description="Start a new chat session"),
            types.BotCommand(command="change_model", description="Change model"),
        ]
    )
    log.info("starting bot")
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    await dp.start_polling(mybot)


if __name__ == "__main__":

    asyncio.run(main(bot))
