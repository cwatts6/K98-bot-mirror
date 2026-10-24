import asyncio
import logging

logger = logging.getLogger(__name__)


import discord


async def wait_with_reminder(
    bot, prompt: str, user_id: int, timeout: int = 3600, remind_after: int = 2700
):
    reminder_sent = asyncio.Event()

    async def reminder():
        await asyncio.sleep(remind_after)
        if not reminder_sent.is_set():
            try:
                user = await bot.fetch_user(user_id)
                dm = await user.create_dm()
                await dm.send(f"⏰ Reminder: I'm still waiting for your input for: **{prompt}**")
                logger.info("Sent timeout reminder DM.")
            except Exception as e:
                logger.warning(f"Failed to send reminder DM: {e}")
            reminder_sent.set()

    task = asyncio.create_task(get_user_input(bot, prompt, user_id, timeout))
    reminder_task = asyncio.create_task(reminder())

    result = await task
    reminder_sent.set()  # Cancel reminder if input received in time
    reminder_task.cancel()

    return result


# === Prompt Admin for Inputs via DM ===
async def get_user_input(bot, prompt: str, user_id: int, timeout: int = 3600):
    try:
        user = await bot.fetch_user(user_id)
        logger.info(f"Fetched user {user.name} ({user.id}) for prompt.")
    except discord.NotFound:
        logger.error(f"User ID {user_id} not found – cannot send DM prompt.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {e}")
        return None

    try:
        dm_channel = await user.create_dm()
        await dm_channel.send(prompt)
        logger.info(f"Sent DM prompt: {prompt}")

        def check(m: discord.Message):
            return m.author.id == user_id and isinstance(m.channel, discord.DMChannel)

        response = await bot.wait_for("message", check=check, timeout=timeout)
        logger.info(f"Received input from user: {response.content}")
        return response.content.strip()
    except TimeoutError:
        await dm_channel.send("⏳ Timed out. No input received.")
        logger.warning("Timed out waiting for user response.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_user_input: {e}")
        return None
