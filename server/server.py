import json
import os
import asyncio
import logging
from random import randint
from dotenv import load_dotenv

# from user import user_left
# from actions import action_get_rooms, action_join_room, action_join, action_message

load_dotenv()

config = {
    "SERVER_IP": os.getenv("SERVER_IP"),
    "SERVER_PORT": os.getenv("SERVER_PORT"),
}

SERVER_IP = config["SERVER_IP"]
SERVER_PORT = int(config["SERVER_PORT"])

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, filemode='w', filename='/var/log/chat_room/server.log')

global USERS
global ROOMS

USERS = {}
ROOMS = {
    "room1": {
        "name": "room1",
        "nb_users": 0,
    }
}

if (not os.path.exists("history.json")):
    with open("history.json", "w") as f:
        json.dump({}, f)

def check_user_in_message(message: str, username) -> bool:
    search = f"@{username}"
    searchEveryone = "@everyone"
    if (search in message or searchEveryone in message):
        return True
    else:
        return False

def get_rooms() -> list:
    rooms_list = {}
    for room in ROOMS:
        rooms_list[room] = ROOMS[room]["nb_users"]
    return rooms_list

def create_room(room: str) -> None:
    ROOMS[room] = {
        "name": room,
        "nb_users": 0,
    }
    with open("history.json", "r") as f:
        data = json.load(f)
        data[room] = {
            "messages": [],
        }
    with open("history.json", "w") as f:
        json.dump(data, f)

def restore_history(room: str) -> list:
    with open("history.json", "r") as f:
        data = json.load(f)
        return data[room]["messages"]

create_room("room1")

async def handle_client(reader, writer):
    while True:
        try:
            data = await reader.read(1024)
            addr = writer.get_extra_info('peername')

            if not data:
                break

            data = json.loads(data.decode())

            if (data['action'] == 'get_rooms'):
                idUser = next((user for user in USERS if USERS[user]["id"] == data["id"]), None)
                print(f"{USERS[idUser]['username']} requested rooms")
                writer.write(json.dumps({
                    "action": "get_rooms",
                    "rooms": get_rooms(),
                }).encode())
                await writer.drain()

            if (data['action'] == 'join_room'):
                user = next((user for user in USERS if USERS[user]["id"] == data["id"]), None)
                USERS[user]["room"] = data["room"]
                if (data["room"] not in ROOMS):
                    create_room(data["room"])
                ROOMS[data["room"]]["nb_users"] += 1
                print(f"{USERS[user]['username']} joined room {data['room']}")
                await user_joined(data["id"])
                USERS[user]["w"].write(json.dumps({
                    "action": "history",
                    "messages": restore_history(data["room"]),
                }).encode())
                await USERS[user]["w"].drain()

            if (data['action'] == 'join'):
                idUser = next((user for user in USERS if USERS[user]["id"] == data["id"]), None)
                if (idUser is None):
                    USERS[addr] = {
                        "r": reader,
                        "w": writer,
                        "username": data["username"],
                        "id": data["id"],
                        "is_connected": True,
                        "room": data["room"],
                        "color": [randint(0, 255), randint(0, 255), randint(0, 255)],
                    }
                    print(f"\033[38;2;{USERS[addr]['color'][0]};{USERS[addr]['color'][1]};{USERS[addr]['color'][2]}m{USERS[addr]['username']}\033[0m connected!")
                    writer.write(json.dumps({
                        "action": "confirm_join",
                        "username": data["username"],
                        "color": USERS[addr]["color"],
                    }).encode())
                    await writer.drain()
                else:
                    USERS[idUser]["is_connected"] = True
                    USERS[idUser]["w"] = writer
                    USERS[idUser]["r"] = reader
                    USERS[idUser]["room"] = data["room"]
                    print(f"\033[38;2;{USERS[idUser]['color'][0]};{USERS[idUser]['color'][1]};{USERS[idUser]['color'][2]}m{USERS[idUser]['username']}\033[0m reconnected!")
                    writer.write(json.dumps({
                        "action": "confirm_join",
                        "username": data["username"],
                        "color": USERS[idUser]["color"],
                    }).encode())
                    await writer.drain()

                logging.info(f"{USERS[addr]['username']} connected!")

            if (data['action'] == 'message'):
                print(f"\033[38;2;{USERS[addr]['color'][0]};{USERS[addr]['color'][1]};{USERS[addr]['color'][2]}m{USERS[addr]['username']}\033[0m: {data['message']}")
                if (data["message"].startswith("/p")):
                    private = data["message"].split(' ')[1]
                    message = data["message"].split(' ', 2)[2]
                    user_to_send = next((user for user in USERS if USERS[user]["username"] == private), None)
                    if (user_to_send is None):
                        continue
                    if (USERS[user_to_send]["room"] != USERS[addr]["room"]):
                        continue
                    USERS[user_to_send]["w"].write(json.dumps({
                        "action": "message",
                        "username": data["username"],
                        "message": message,
                        "color": USERS[addr]["color"],
                        "private": True,
                        "mention": check_user_in_message(message, USERS[user_to_send]["username"]),
                    }).encode())
                    await USERS[user_to_send]["w"].drain()

                elif (not data["message"].startswith("/p")):
                    for user in USERS:
                        if (USERS[user]["username"] == data["username"] or USERS[user]["is_connected"] == False):
                            continue
                        if (USERS[user]["room"] != USERS[addr]["room"]):
                            continue
                        USERS[user]["w"].write(json.dumps({
                            "action": "message",
                            "username": data["username"],
                            "message": data["message"],
                            "color": USERS[addr]["color"],
                            "private": False,
                            "mention": check_user_in_message(data["message"], USERS[user]["username"]),
                        }).encode())
                        await USERS[user]["w"].drain()

                    logging.info(f"{USERS[addr]['username']}: {data['message']}")

                    with open("history.json", "r") as f:
                        file = json.load(f)
                        file[USERS[addr]["room"]]["messages"].append({
                            "username": data["username"],
                            "message": data["message"],
                            "color": USERS[addr]["color"],
                            "mention": check_user_in_message(data["message"], USERS[user]["username"]),
                        })
                    with open("history.json", "w") as f:
                        json.dump(file, f)

        except Exception as e:
            print('Error communicating with {}: {}'.format(addr, e))
            break

    await user_left(USERS[addr]["username"])

    if (addr in USERS):
        USERS[addr]["w"].close()
        USERS[addr]["is_connected"] = False

    print(f"{USERS[addr]['username']} disconnected!")
    logging.info(f"{USERS[addr]['username']} disconnected!")

async def user_joined(user_id):
    speUser = next((user for user in USERS if USERS[user]["id"] == user_id), None)
    for user in USERS:
        if (USERS[user]["id"] == user_id or USERS[user]["is_connected"] == False):
            continue
        if (USERS[user]["room"] != USERS[speUser]["room"]):
            continue
        USERS[user]["w"].write(json.dumps({
            "action": "user_joined",
            "username": USERS[speUser]["username"],
            "color": USERS[speUser]["color"],
        }).encode())
        await USERS[user]["w"].drain()

async def user_left(username: str):
    speUser = next((user for user in USERS if USERS[user]["username"] == username), None)
    if (USERS[speUser]["room"] not in ROOMS or ROOMS[USERS[speUser]["room"]] == "general"):
        return
    ROOMS[USERS[speUser]["room"]]["nb_users"] -= 1
    for user in USERS:
        if (USERS[user]["username"] == username or USERS[user]["is_connected"] == False):
            continue
        if (USERS[user]["room"] != USERS[speUser]["room"]):
            continue
        # if (ROOMS[USERS[user]["room"]]["nb_users"] >= 0):
        #     del ROOMS[USERS[user]["room"]]
        USERS[user]["w"].write(json.dumps({
            "action": "user_left",
            "username": username,
            "color": USERS[speUser]["color"],
        }).encode())
        await USERS[user]["w"].drain()

class Server:
    def __init__(self) -> None:
        self._server = None
        self._addrs = None

    async def start(self):
        try:
            self._server = await asyncio.start_server(handle_client, SERVER_IP, SERVER_PORT)
            self._addrs = ', '.join(str(socket.getsockname()) for socket in self._server.sockets)
            print(f'\033[32;1mServing on {self._addrs} \033[0m')

            async with self._server:
                await self._server.serve_forever()
        except KeyboardInterrupt:
            print('\033[31;1mServer stopped by user\033[0m')

    def close(self):
        self._server.sockets.close()

if __name__ == '__main__':
    server: Server = Server()
    asyncio.run(server.start())
