"""
STATUS: Code is working. ❎
"""

"""
BSD 2-Clause License

Copyright (C) 2022, SOME-1HING [https://github.com/SOME-1HING]

Credits:-
    Copyright (C) 2017-2019, Paul Larsen
    Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
    Copyright (c) 2021-2022, Copyright (c) 2021 TheHamkerCat    

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from os import remove
from pyrogram import filters

from Shikimori import BOT_USERNAME, DEV_USERS, arq, pbot
from Shikimori.utils.errors import capture_err
from Shikimori.utils.permissions import adminsOnly
import Shikimori.modules.sql.nsfw_sql as sql

async def get_file_id_from_message(message):
    file_id = None
    if message.document:
        if int(message.document.file_size) > 3145728:
            return
        mime_type = message.document.mime_type
        if mime_type not in ("image/png", "image/jpeg"):
            return
        file_id = message.document.file_id

    if message.sticker:
        if message.sticker.is_animated:
            if not message.sticker.thumbs:
                return
            file_id = message.sticker.thumbs[0].file_id
        else:
            file_id = message.sticker.file_id

    if message.photo:
        file_id = message.photo.file_id

    if message.animation:
        if not message.animation.thumbs:
            return
        file_id = message.animation.thumbs[0].file_id

    if message.video:
        if not message.video.thumbs:
            return
        file_id = message.video.thumbs[0].file_id
    return file_id


@pbot.on_message(
    (
        filters.document
        | filters.photo
        | filters.sticker
        | filters.animation
        | filters.video
    ),
    group=8,
)
@capture_err
async def detect_nsfw(_, message):
    chat_id = message.chat.id
    is_nsfw = sql.is_nsfw(chat_id)
    if not is_nsfw:
        return
    if is_nsfw:
        pass
    if not message.from_user:
        return
    file_id = await get_file_id_from_message(message)
    if not file_id:
        return
    file = await pbot.download_media(file_id)
    try:
        results = await arq.nsfw_scan(file=file)
    except Exception:
        return
    if not results.ok:
        return
    results = results.result
    remove(file)
    nsfw = results.is_nsfw
    if message.from_user.id in DEV_USERS:
        return
    if not nsfw:
        return
    try:
        await message.delete()
    except Exception:
        return
    await message.reply_text(
        f"""
**NSFW Image Detected & Deleted Successfully!
————————————————————**
**User:** {message.from_user.mention} [`{message.from_user.id}`]
**Safe:** `{results.neutral} %`
**Porn:** `{results.porn} %`
**Adult:** `{results.sexy} %`
**Hentai:** `{results.hentai} %`
**Drawings:** `{results.drawings} %`
**————————————————————**
__Powered by__@Yuki_Network.
"""
    )


@pbot.on_message(filters.command(["nsfwscan", "nsfwscan@Shikimori"]))
@capture_err
async def nsfw_scan_command(_, message):
    if not message.reply_to_message:
        await message.reply_text(
            "Reply to an image/document/sticker/animation to scan it."
        )
        return
    reply = message.reply_to_message
    if (
        not reply.document
        and not reply.photo
        and not reply.sticker
        and not reply.animation
        and not reply.video
    ):
        await message.reply_text(
            "Reply to an image/document/sticker/animation to scan it."
        )
        return
    m = await message.reply_text("Scanning")
    file_id = await get_file_id_from_message(reply)
    if not file_id:
        return await m.edit("Something wrong happened.")
    file = await pbot.download_media(file_id)
    try:
        results = await arq.nsfw_scan(file=file)
    except Exception:
        return
    remove(file)
    if not results.ok:
        return await m.edit(results.result)
    results = results.result
    await m.edit(
        f"""
**Neutral:** `{results.neutral} %`
**Porn:** `{results.porn} %`
**Hentai:** `{results.hentai} %`
**Sexy:** `{results.sexy} %`
**Drawings:** `{results.drawings} %`
**NSFW:** `{results.is_nsfw}`
"""
    )


@pbot.on_message(filters.command(["antinsfw", f"antinsfw@{BOT_USERNAME}"]))
@adminsOnly("can_change_info")
async def nsfw_enable_disable(_, message):
    if len(message.command) != 2:
        await message.reply_text(
            "Usage: /antinsfw [on/off]"
        )
        return
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id
    if status in ("on", "yes"):
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            sql.set_nsfw(chat_id)
            await message.reply_text(
            "Enabled AntiNSFW System. I will Delete Messages Containing Inappropriate Content."
            )
        message.reply_text("NSFW Mode is already Activated for this chat!")
        return ""
    elif status in ("off", "no"):
        if not is_nsfw:
            message.reply_text("NSFW Mode is already Deactivated")
            return ""
        else:
            sql.rem_nsfw(chat_id)
            await message.reply_text("Disabled AntiNSFW System.")
    else:
        await message.reply_text(
            "Unknown Suffix, Use /antinsfw [on/off]"
        )