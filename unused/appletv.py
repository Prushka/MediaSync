"""Example of streaming a file and printing status updates.
python stream.py 10.0.0.4 file.mp3
"""

import asyncio
import sys
import time

import pyatv
from pyatv.interface import Playing, PushListener
from pyatv.const import Protocol

import settings
from MediaPlayer import ATVPlayer

LOOP = asyncio.get_event_loop()

stored_credentials = {
    Protocol.AirPlay: "7b94d5a12e48e0e8b6697082a225597f4197acec65b300d04a16da6b2891150f:1af77407a12e07c40b778e62cb1aaa4190bf2e07236cf0813a77fe362f52b5b9:41333435453544302d364244372d344436322d413332362d393046304237424532424137:61323364326632662d303566322d343830362d383362312d613836613234393231646537",
    Protocol.RAOP: "1390f60fa77eb404c20c75dcc980a2bef268f343a3b7892137d5fadb64f33499::e1b83cd3a3619a42",
    Protocol.Companion: "7b94d5a12e48e0e8b6697082a225597f4197acec65b300d04a16da6b2891150f:34fb60ff68baeeacbe67686dc5a8fe88ec05eb13f55e827cdefcba99fbaf27dd:41333435453544302d364244372d344436322d413332362d393046304237424532424137:37313735386663322d636665352d343866302d623762322d636432396361323932623530"}


async def run(loop: asyncio.AbstractEventLoop):
    """Find a device and print what is playing."""
    print("* Discovering device on network...")
    atvs = await pyatv.scan(loop)
    for atv in atvs:
        if atv.name == "ATV":
            for protocol, credentials in stored_credentials.items():
                atv.set_credentials(protocol, credentials)
            print(atv.device_info.model)
            a = await pyatv.connect(atv, loop)
            init_state = await a.metadata.playing()
            settings.atv = ATVPlayer(a, init_state)
            a.push_updater.listener = settings.atv
            a.push_updater.start()
            print("Press ENTER to quit")
            await loop.run_in_executor(None, sys.stdin.readline)
            a.close()
            break


if __name__ == "__main__":
    LOOP.run_until_complete(run(LOOP))
