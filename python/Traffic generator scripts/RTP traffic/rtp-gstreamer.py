import gi
import random
import time
import threading
import asyncio
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)


target_ips = [f"10.0.4.{i}" for i in range(1, 11)]


def initiate_call(target_ip):
    pipeline = Gst.parse_launch(
        f"audiotestsrc wave=sine ! audioconvert ! audioresample ! opusenc ! rtpopuspay ! udpsink host={target_ip} port=5000"
    )
    pipeline.set_state(Gst.State.PLAYING)
    time.sleep(random.randint(10, 60))
    pipeline.set_state(Gst.State.NULL)

def receive_call():
    pipeline = Gst.parse_launch(
        "udpsrc port=5000 caps=\"application/x-rtp, media=audio, encoding-name=OPUS, payload=96\" ! "
        "rtpopusdepay ! opusdec ! audioconvert ! audioresample ! autoaudiosink"
    )
    pipeline.set_state(Gst.State.PLAYING)
    while True:
        time.sleep(1)

async def manage_calls():
    while True:
        tasks = []
        for _ in range(5):
            target_ip = random.choice(target_ips)
            task = asyncio.to_thread(initiate_call, target_ip)
            tasks.append(asyncio.create_task(task))
            await asyncio.sleep(random.randint(1, 5))
        await asyncio.gather(*tasks)

def main():
    threading.Thread(target=receive_call, daemon=True).start()
    asyncio.run(manage_calls())

if __name__ == "__main__":
    main()
