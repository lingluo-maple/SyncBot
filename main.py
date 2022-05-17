from io import BytesIO
import logging
import asyncio
from pathlib import Path
from typing import List

import filetype
from loguru import logger
from graia.ariadne import Ariadne
from graia.ariadne.app import MiraiSession
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import (
    Plain,
    Image,
    Face,
    Quote,
    Source,
    At,
    AtAll,
    File,
    Forward,
    ForwardNode,
)
from graia.ariadne.event.lifecycle import ApplicationShutdowned
from graia.ariadne.event.message import GroupMessage, ActiveMessage
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.ariadne.exception import RemoteException
from graia.ariadne.model import Member, Group
from graia.broadcast import Broadcast
from telethon import TelegramClient
from telethon import events
from telethon.tl.types import (
    User,
    Message,
    MessageMediaDocument,
    MessageMediaPhoto,
    Document,
    DocumentAttributeFilename,
)
from TelethonFakeTLS import ConnectionTcpMTProxyFakeTLS

import sql
from utils import webp2png, mp42gif, parseMessageChain
from config import config, groups

logging.basicConfig(
    level=logging.INFO, format="TELETHON: %(asctime)s - %(levelname)s | %(message)s"
)

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
ariadne = Ariadne(
    MiraiSession(
        host="http://localhost:8080/",
        account=config.account,
        verify_key=config.verify_key,
    ),
    loop=loop,
    broadcast=bcc,
    chat_log_config=False,
)
if not config.proxy:
    proxy = tuple()
else:
    proxy = config.proxy
client = TelegramClient(
    "syncBot",
    api_id=config.api_id,
    api_hash=config.api_hash,
    connection=ConnectionTcpMTProxyFakeTLS,
    proxy=proxy,
    loop=loop,
)


class Handler:
    @staticmethod
    @bcc.receiver(GroupMessage)
    async def group_message_handler(
        member: Member, group: Group, message: MessageChain
    ):
        """Graia Ariadne message handleer (QQ)"""
        if not group.id in list(groups.keys()):
            return
        logger.info(f"{member.name} said: '{message.asDisplay()}' in QQ")
        await Forwarder.qq2tg(member, message)

    @staticmethod
    @bcc.receiver(GroupRecallEvent)
    async def recall_handler(member: Member, group: Group):
        if not group.id in list(groups.keys()):
            return

    @staticmethod
    @client.on(events.NewMessage())
    async def handler(event):
        """Telethon message handleer (Telegram)"""
        sender: User = event.sender
        if not sender:
            logging.info(f"匿名管理员发言")
            return
        message: Message = event.message
        name = (
            sender.first_name + sender.last_name
            if sender.first_name and sender.last_name
            else sender.first_name or sender.last_name
        )
        logging.info(f"{name} said: '{message.message}' in Telegram")
        logging.debug(f"Message: {message}")
        await Forwarder.tg2qq(sender, message, event.chat_id)

    @staticmethod
    @client.on(events.NewMessage(pattern=r"get_id"))
    async def getId(event):
        logging.info(type(event))
        chat_id = event.chat_id
        logging.info(f"Chat: {chat_id}")
        await event.reply(f"Chat: {chat_id}")


class Forwarder:
    @staticmethod
    async def qq2tg(member: Member, message: MessageChain):
        """Send message from qq to telegram
        logger: loguru.logger
        """
        TGgroup = groups.getTGGroup(member.group.id)
        messageId = message.getFirst(Source).id
        sender = f"[{member.name}]"
        logger.info(
            f"Plain: {message.has(Plain)}, At: {message.has(At)}, AtAll: {message.has(AtAll)}, Image: {message.has(Image)}, Quote: {message.has(Quote)}, Forward: {message.has(Forward)}, Face: {message.has(Face)}"
        )
        if message.has(File):
            # 文件只会单独出现
            file = message.getFirst(File)
            size = file.size
            if size / 1024 / 1024 > 10 or True:
                # 不支持下载文件
                logger.info(f"File：{size / 1024 / 1024}MB")
                await client.send_message(TGgroup, f"`{sender}: File[id={file.id}, name={file.name}, size={size / 1024 / 1024}MB]`")  # type: ignore
                return
        elif message.has(Forward):
            # 合并转发
            logger.info(f"{message.asDisplay()}")
            images = None
            forward = message.getFirst(Forward)
            nodes = forward.nodeList
            response = await client.send_message(TGgroup, f"`{message.asDisplay()}`")  # type: ignore
            logger.info(f"Append to database: QQ-{messageId} <-> TG-{response.id}")
            sql.append(messageId, response.id)
        else:
            nodes = [message]
        for i in range(len(nodes)):
            node = nodes[i]
            if isinstance(node, ForwardNode):
                if node.messageChain:
                    message = node.messageChain
                    sender = f"[合并转发: {node.senderId}]"
            else:
                message = node
            result = await parseMessageChain(message)
            text = result.text
            images = result.images
            tgId = result.tgId
            if images:
                response = await client.send_file(TGgroup, images, caption=f"**`{sender}:`**{text}", parse_mode="markdown", reply_to=tgId)  # type: ignore
            else:
                response = await client.send_message(TGgroup, f"**`{sender}` **{text}", parse_mode="markdown", reply_to=tgId)  # type: ignore
            if isinstance(response, List):
                # send_file 返回 List[Message]
                for msg in response:
                    logger.info(f"Append to database: QQ-{messageId} <-> TG-{msg.id}")
                    sql.append(messageId, msg.id)
            else:
                logger.info(f"Append to database: QQ-{messageId} <-> TG-{response.id}")
                sql.append(messageId, response.id)

    @staticmethod
    async def tg2qq(sender: User, message: Message, origin: int):
        QQgroup = groups.getQQGroup(origin)
        name = (
            sender.first_name + sender.last_name
            if sender.first_name and sender.last_name
            else sender.first_name or sender.last_name
        )
        msgChain = MessageChain.create()
        if message.reply_to:
            messageId = sql.queryByTgId(message.reply_to)
            msgChain.append(
                Quote(
                    id=messageId,
                    groupId=QQgroup,
                    senderId=ariadne.account if ariadne.account else 0,
                    targetId=QQgroup,
                    origin=MessageChain.create(),
                )
            )
        msg = message.message
        msgChain.append(Plain(msg))
        logger.debug(f"Message:\n {message}")
        if not isinstance(media := message.media, MessageMediaDocument) or isinstance(media, MessageMediaPhoto):
            logger.error(f"Unsupport media type: {type(media)}")
            return
        filename = ""

        if (isinstance(media, MessageMediaDocument) 
            and isinstance(media.document, Document)):
            # 跳过大文件
            document = media.document
            size = document.size
            if not (filename := [
                attr.file_name
                for attr in document.attributes
                if isinstance(attr, DocumentAttributeFilename)
            ]):
                logger.error("File name not found")
            filename = filename[0]
            if size / 1024 / 1024 > 10:
                logger.info(f"{name} sent a large file {size / 1024 / 1024}MB")
                msgChain.append(
                    Plain(f"File[name={filename}, {size / 1024 / 1024}MB]")
                )
                await ariadne.sendGroupMessage(QQgroup, msgChain)
                return
            elif filename.endswith(".gif.mp4"):
                logger.info(f"{name} sent a gif {size / 1024}KB")
            elif not document.mime_type.startswith("image"):
                # 上传小文件
                if not isinstance(tempFile := await client.download_media(message, file=BytesIO()), BytesIO):
                    logger.error(f"Type Error: tempFile is {type(tempFile)}")
                    return
                else:
                    tempFile = tempFile.getvalue()
                logger.info(f"{name} sent a file {media.document.size / 1024 / 1024:.2f}MB")
                try:
                    await ariadne.uploadFile(tempFile, method="group", target=QQgroup, name=filename)
                except RemoteException as e:
                    logger.error(f"{e}")
                    await client.send_message(origin, f"上传文件失败: `{e}`")  # type: ignore
                return
        
        # 通过检测 下载文件
        if not isinstance(tempFile := await client.download_media(message, file=BytesIO()), BytesIO):
            logger.error(f"Type Error: tempFile is {type(tempFile)}")
            return
        else:
            tempFile = tempFile.getvalue()
        # 非Document 或 通过检测
        if filetype.guess_mime(tempFile) is not None:
            # 文件为图片类型，添加至消息链
            mime = filetype.guess_mime(tempFile)
            if not isinstance(mime, str):
                return
            if mime == "video/mp4" and filename.endswith(".gif.mp4"):
                # mp4 to gif
                with open("tmp.mp4", "wb") as f:
                    f.write(tempFile)
                Path("tmp.gif").touch()
                mp42gif("tmp.mp4", "tmp.gif")
                tempFile = Path("tmp.gif").read_bytes()
                mime = "image/gif"
            if mime.startswith("image"):
                if mime.endswith("webp"):
                    tempFile = webp2png(tempFile)
                mime = filetype.guess_mime(tempFile)
                logging.info(f"Image type: {mime}")
                msgChain.append(Image(data_bytes=tempFile))
        logging.info(f"msgChain: {msgChain}")
        if not msgChain:
            logging.info("MessageChain is Empty")
            return
        msg = await ariadne.sendGroupMessage(QQgroup, msgChain)
        if msg.messageId < 0:
            logging.warning("账号可能被风控")
            await client.send_message(origin, "消息发送失败，账号可能被风控", reply_to=message)  # type: ignore


async def main():
    await ariadne.launch()
    await client.disconnected


if __name__ == "__main__":
    client.start(bot_token=config.bot_token)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        bcc.postEvent(ApplicationShutdowned(ariadne))
        loop.run_until_complete(ariadne.stop())
        client.disconnect()
