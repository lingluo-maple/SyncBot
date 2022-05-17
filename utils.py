import os
import subprocess
from io import BytesIO
from typing import List, Optional

from loguru import logger
from graia.ariadne import Ariadne
from graia.ariadne.exception import RemoteException
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, AtAll, Face, Image, Plain, Quote
from PIL import Image as PILImage
from pydantic import BaseModel
from telethon.tl.types import Document

import sql


class Result(BaseModel):
    text: Optional[str]
    images: Optional[List]
    tgId: Optional[int]

def webp2png(webp: bytes) -> bytes:
    """Convert webp to png"""
    img = PILImage.open(BytesIO(webp))
    png = BytesIO()
    img.save(png, format="png")
    return png.getvalue()

async def parseMessageChain(message: MessageChain) -> Result:
    if (
        message.has(Plain)
        or message.has(Face)
        or message.has(At)
        or message.has(AtAll)
    ):
        text = " " + "".join(
            [
                x.asDisplay()
                for x in message
                if isinstance(x, Plain)
                or isinstance(x, Face)
                or isinstance(x, At)
                or isinstance(x, AtAll)
            ]
        )
    else:
        text = ""
    if message.has(Image):
        images = [await image.get_bytes() for image in message.get(Image)]
    else:
        images = None
    if message.has(Quote):
        quoteId = message.getFirst(Quote).id
        tgId = sql.queryByQQId(quoteId)
    else:
        tgId = None
    return Result(text=text, images=images, tgId=tgId)

def mp42gif(in_file_path, out_file_path):
    palette_path = out_file_path.replace(".gif", "_palette.png")
    command = 'ffmpeg -y -i %(mp4)s -vf fps=10,scale=-1:-1:flags=lanczos,palettegen %(palette)s'
    command = command % {'mp4': in_file_path, 'palette': palette_path}
    result = subprocess.run(f"{command} > /dev/null 2>&1", shell=True)
    if result.returncode != 0:
        os.path.isfile(palette_path)
        os.remove(palette_path)
        logger.error(f"ffmpeg error: {result.returncode}")
        raise Exception('ffmpeg error: execute gif => _palette.png')

    command = 'ffmpeg -y -i %(mp4)s -i %(palette)s -filter_complex "fps=10,scale=-1:-1:flags=lanczos[x];[x][1:v]paletteuse" %(gif)s'
    command = command % {'mp4': in_file_path, 'palette': palette_path, 'gif': out_file_path}
    result = subprocess.run(f"{command} > /dev/null 2>&1", shell=True, encoding="utf8")
    os.path.isfile(palette_path)
    os.remove(palette_path)
    if result.returncode != 0:
        raise Exception('ffmpeg error: execute .gif => .mp4')
    else:
        return out_file_path