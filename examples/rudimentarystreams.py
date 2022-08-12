import asyncio
import logging
import os

import dotenv

from glasses3 import connect_to_glasses

logging.basicConfig(level=logging.INFO)


async def subscribe_to_signal():

    async with connect_to_glasses(os.environ["G3_HOSTNAME"]) as g3:
        imu_queue, unsubscribe = await g3.rudimentary.subscribe_to_imu()

        async def imu_receiver():
            count = 0
            while True:
                imu_message = await imu_queue.get()
                count += 1
                if count % 300 == 0:
                    logging.info(f"Received {count} messages")
                    logging.info(f"Message snapshot: {imu_message}")
                imu_queue.task_done()

        await g3.rudimentary.start_streams()
        receiver = asyncio.create_task(imu_receiver(), name="imu_receiver")
        await asyncio.sleep(12)
        await g3.rudimentary.stop_streams()
        await imu_queue.join()
        receiver.cancel()
        await unsubscribe


def main():
    asyncio.run(subscribe_to_signal())


if __name__ == "__main__":
    dotenv.load_dotenv()
    main()