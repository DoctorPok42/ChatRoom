import json
from random import randint

from user import user_joined
from server import get_rooms, create_room, restore_history, check_user_in_message
from server import USERS, ROOMS

async def action_get_rooms(writer, data):
    idUser = next((user for user in USERS if USERS[user]["id"] == data["id"]), None)
    print(f"{USERS[idUser]['username']} requested rooms")
    writer.write(json.dumps({
        "action": "get_rooms",
        "rooms": get_rooms(),
    }).encode())
    await writer.drain()

async def action_join_room(writer, data):
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

async def action_join(writer, reader, addr, data):
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

async def action_message(writer, reader, addr, data):
    print(f"\033[38;2;{USERS[addr]['color'][0]};{USERS[addr]['color'][1]};{USERS[addr]['color'][2]}m{USERS[addr]['username']}\033[0m: {data['message']}")
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
            "mention": check_user_in_message(data["message"], USERS[user]["username"]),
        }).encode())
        await USERS[user]["w"].drain()

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