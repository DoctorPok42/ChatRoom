import json

from server import USERS, ROOMS

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
        if (ROOMS[USERS[user]["room"]]["nb_users"] >= 0):
            del ROOMS[USERS[user]["room"]]
        USERS[user]["w"].write(json.dumps({
            "action": "user_left",
            "username": username,
            "color": USERS[speUser]["color"],
        }).encode())
        await USERS[user]["w"].drain()
