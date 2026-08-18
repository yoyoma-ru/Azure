"""Azure Relay Hybrid Connections センダー（Send 権限）。

connect＝リスナーへ向けて接続を開始し、メッセージを送る（教材 W3/W4）。
使い方: python sender.py "送りたいテキスト"
"""
import asyncio
import json
import logging
import sys

import websockets

import relaylib
from config import load


async def main(text: str) -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load()
    token = relaylib.create_sas_token(cfg["namespace"], cfg["path"], cfg["key_name"], cfg["key"])
    url = relaylib.create_send_url(cfg["namespace"], cfg["path"], token)
    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"message": text}))
        logging.info("sent: %s", text)


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "Hello from Azure Relay!"
    asyncio.run(main(msg))
