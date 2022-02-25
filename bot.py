from asyncio import sleep
from pydoc import cli
import client,time

drip_cli = client.DripBot()

drip_cli.start()

# keep waiting
while True:
    try:
        time.sleep(1)
    except:
        print("\nExiting...")
        exit()
    
