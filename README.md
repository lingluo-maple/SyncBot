# QQ-TG forward bot

用于将QQ群组与TG群组的消息进行同步互通

由于使用的两个bot库分别使用了下划线命名法与驼峰命名法，所以代码可读性可能有点感人

~~写的很渣，欢迎PR~~

## 支持转发类型
- 文本消息
- 图片
- GIF
- 文件 (仅支持tg->qq)
- QQ Face
- 回复消息
- 合并转发 (单层 多图会导致延迟严重)

## 依赖库
- graia-ariadne: QQ 机器人框架
- Telethon: Telegram 机器人框架
- sqlalchemy: 提供ORM SQL，用于增加，查询 QQ-message-id 与 Telegram-message-id 的映射关系
- TelethonFakeTls: 提供 MTProto V3 Proxy 支持 (由于上游仓库没合并PR 所以就直接扔本地了)
- filetype: 用于检测从Telegram下载下的文件类型
- Pillow: 用于将从Telegram下载下的webp格式图片转换为png格式 (QQ仅支持 gif/png/jpg/bmp)
- cryptg: [可选] Telethon官方介绍的可加快下载速度的库 可输入`poetry add telethon[crtptg]`添加

## 其他依赖
- ffmpeg: 用于将mp4转为gif

## 使用

本项目使用 `pypoetry` 进行包管理

### 1.安装Python

安装方式见百度，安装成功后在命令行输入 `python -V` 后会显示python版本号，建议使用`Python3.9`

### 2.安装poetry

```bash
python -m pip install poetry
```

### 3.安装依赖项

首先确保当前工作目录位于项目目录下 (目录下存在`pyproject.toml`与`poetry.lock`), 然后输入

```bash
python -m poetry install
```

等待安装完成

### 4.更改配置文件

打开`config.example.py`文件 在`config=`中输入你的相关配置
|          项目名               |             说明            |
| ---------------------------- | --------------------------- |
|    account      |           QQ机器人账号                   |
|   verify_key    | 与下文 mirai-api-http verify_key 保持一致 |
|   api_key       | 从 my.telegram.org 获取的api_id          |
|   api_hash      | 从 my.telegram.org 获取的api_hash        |
|   bot_token     |    从 @botfather 获取的bot_token         |
|   proxy (可选)  |  连接 Telegram 服务器时所使用的代理        |

在 `groups=` 中输入需要转发的 QQ群号: TG群id

TG群id可将bot拉入群聊并给予权限后发送`get_id`获得

### 5.配置 mirai-api-http

请参考 https://github.com/project-mirai/mirai-api-http#%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8

### 6.启动

为了使程序在退出ssh后依旧运行，则需使用`screen`等程序

此处使用`screen`

```bash
screen -S syncBot
python -m poetry use python3.9
python main.py
```

然后输入 `Ctrl+A` + `D`

输入`screen -x syncBot`返回

