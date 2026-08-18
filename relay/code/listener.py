"""Azure Relay Hybrid Connections リスナー（Listen 権限・学習用の最小形）。

listen＝コントロールチャネルを張って待ち受ける（教材 W3）。
本番強度のリスナーは accept 通知→ランデブーソケットのハンドシェイクまで扱う。
その完全実装は公式 SDK（.NET/Node hyco-ws）に委ねるのが実務判断（教材 W7/W8）。
"""
import asyncio
import logging

import websockets

import relaylib
from config import load


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load()
    token = relaylib.create_sas_token(cfg["namespace"], cfg["path"], cfg["key_name"], cfg["key"])
    url = relaylib.create_listen_url(cfg["namespace"], cfg["path"], token)
    async with websockets.connect(url) as ws:
        logging.info("listening on %s / %s", cfg["namespace"], cfg["path"])
        while True:
            message = await ws.recv()
            logging.info("received: %s", message)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("listener stopped")
