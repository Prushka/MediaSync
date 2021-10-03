import asyncio
from ipaddress import IPv4Address
from pprint import pprint

import pyatv
from pyatv import scan, pair, conf
from pyatv.const import Protocol

import const

stored_credentials = {
    Protocol.AirPlay: "7b94d5a12e48e0e8b6697082a225597f4197acec65b300d04a16da6b2891150f:1af77407a12e07c40b778e62cb1aaa4190bf2e07236cf0813a77fe362f52b5b9:41333435453544302d364244372d344436322d413332362d393046304237424532424137:61323364326632662d303566322d343830362d383362312d613836613234393231646537",
    Protocol.RAOP: "1390f60fa77eb404c20c75dcc980a2bef268f343a3b7892137d5fadb64f33499::e1b83cd3a3619a42",
    Protocol.Companion: "7b94d5a12e48e0e8b6697082a225597f4197acec65b300d04a16da6b2891150f:34fb60ff68baeeacbe67686dc5a8fe88ec05eb13f55e827cdefcba99fbaf27dd:41333435453544302d364244372d344436322d413332362d393046304237424532424137:37313735386663322d636665352d343866302d623762322d636432396361323932623530"}


async def find_atv(loop):
    atv = None
    atvs = await scan(loop)
    for atv in atvs:
        if atv.name == "ATV":
            atv = atv
            break
    return atv

async def main():
    loop = asyncio.get_event_loop()
    atv = await find_atv(loop)
    pairing = await pair(atv, Protocol.MRP, loop)
    await pairing.begin()

    if pairing.device_provides_pin:
        pin = int(input("Enter PIN: "))
        pairing.pin(pin)
    else:
        pairing.pin(1234)  # Should be randomized
        input("Enter this PIN on the device: 1234")

    await pairing.finish()

    # Give some feedback about the process
    if pairing.has_paired:
        print("Paired with device!")
        print("Credentials:", pairing.service.credentials)
    else:
        print("Did not pair with device!")

    await pairing.close()

    identifier = const.CONF_IDENTIFIERS

    # Save identifier

    #for service in config.services:
    #    protocol = service.protocol
    #    credentials = service.credentials

        # Save mapping of protocol and credentials

async def connect():

    loop = asyncio.get_event_loop()
    atv = await find_atv(loop)
    for protocol, credentials in stored_credentials.items():
        atv.set_credentials(protocol, credentials)
    atv = await pyatv.connect(atv, loop)
    print(atv.device_info.model)
    await atv.remote_control.up()
    playing = await atv.metadata.playing()
    print(playing)


if __name__ == '__main__':
    asyncio.run(connect())  # asyncio.run requires python 3.7+