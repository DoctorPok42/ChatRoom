import socket
import asyncio
import platform
import hashlib
import aioconsole
import json
import logging
from ascii_magic import AsciiArt

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filemode='w', filename='/var/log/chat_room/client.log')

class Client:
    def __init__(self, host: str, port: str, username: str) -> None:
        self._host: str = host
        self._port: str = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._username: str = username
        self._reader: asyncio.StreamReader = None
        self._writer: asyncio.StreamWriter = None
        self._room: str = "general"
        self._state: str = "waiting"
        self._color = [0, 0, 0]
        self._id: str = None

    async def connect(self):
        reader, writer = await asyncio.open_connection(host=self._host, port=self._port)
        self._reader = reader
        self._writer = writer
        await self.join()

    async def join(self):
        self._writer.write(json.dumps({
            "action": "join",
            "username": self._username,
            "room": "general",
            'id': self._id,
        }).encode())
        await self._writer.drain()
        self._state = "connected"

    async def generateID(self):
        myID = platform.node()
        myID = myID + self._username
        myID = hashlib.sha256(myID.encode()).hexdigest()
        self._id = myID

    async def get_rooms(self):
        self._writer.write(json.dumps({
            "action": "get_rooms",
            "id": self._id,
        }).encode())
        await self._writer.drain()
        self._state = "get_rooms"

    async def connect_to_room(self, room: str):
        if (room == ''):
            return
        self._room = room
        self._writer.write(json.dumps({
            "action": "join_room",
            "username": self._username,
            "id": self._id,
            "room": self._room,
        }).encode())
        await self._writer.drain()
        self._state = "connected"

    async def send(self):
        while True:
            message: str = await aioconsole.ainput()
            if (message == ''):
                continue
            if (message == '/exit'):
                exit()
            # if (message == '/rooms'):
            #     await self.choose_room()
            #     print("Please choose a room:")
            #     continue
            # if (message == '/r'):
            #     await self.choose_room()
            #     self._state = "get_rooms"
            #     break

            if (self._state == "get_rooms"):
                break
            else:
                self._writer.write(json.dumps({
                    "action": "message",
                    "id": self._id,
                    "username": self._username,
                    "message": message,
                }).encode())
                await self._writer.drain()

    async def receive(self):
        while True:
            data = await self._reader.read(1024)
            if not data:
                return
            data = json.loads(data.decode())
            if (data['action'] == 'confirm_join'):
                self._color = data['color']
                print("\033c", end="")
                print(f"Your are connected as \033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m!")
                break

            elif (data['action'] == 'history'):
                # print("\033c", end="")
                for message in data['messages']:
                    if (message['mention']):
                        print(f"\033[38;2;{message['color'][0]};{message['color'][1]};{message['color'][2]}m{message['username']}\033[0m: \033[48;2;255;165;0m{message['message']}\033[0m")
                    else:
                        print(f"\033[38;2;{message['color'][0]};{message['color'][1]};{message['color'][2]}m{message['username']}\033[0m: {message['message']}")

            elif (data['action'] == 'user_joined'):
                print(f"\033[3m\033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m \033[3mjoined the chat!\033[0m")
                logging.info(f"{data['username']} joined the chat!")

            elif (data['action'] == 'user_left'):
                print(f"\033[3m\033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m \033[3mleft the chat!\033[0m")
                logging.info(f"{data['username']} left the chat!")

            elif (data['action'] == 'message'):
                if (data['private']):
                    print(f"\033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m (Private): {data['message']}")
                    logging.info(f"{data['username']} (Private): {data['message']}")
                elif (data['mention']):
                    print(f"\033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m: \033[48;2;255;165;0m{data['message']}\033[0m")
                    logging.info(f"{data['username']} (Mention): {data['message']}")
                else:
                    print(f"\033[38;2;{data['color'][0]};{data['color'][1]};{data['color'][2]}m{data['username']}\033[0m: {data['message']}")
                    logging.info(f"{data['username']}: {data['message']}")

            elif (data['action'] == 'message_img'):
                my_art = AsciiArt.from_image(data['image_data'])
                print(my_art.to_ascii())
    def disconnect(self):
        self._socket.close()