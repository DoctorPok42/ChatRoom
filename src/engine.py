import json
import asyncio

from client import Client

async def choose_room(user: Client) -> None:
    await user.get_rooms()

    data = await user._reader.read(1024)
    data = json.loads(data.decode())
    if (data["action"] == "get_rooms"):
        print("Please choose a room:")
        for room in data['rooms']:
            if (room == "general"):
                continue
            print(f"\033[38;2;255;165;0m- {room} ({data['rooms'][room]} users)\033[0m")

        room = input("Room: ")
        await user.connect_to_room(room)
        print("\033c", end="")
        print(f"Your are connected as \033[38;2;{user._color[0]};{user._color[1]};{user._color[2]}m{user._username}\033[0m in Room\033[3;1m {user._room}\033[0m!")

class Engine:
    def __init__(self, config: dict = {}, username: str = "") -> None:
        self._config = config
        self._user: Client = Client(config["SERVER_HOST"], int(config["SERVER_PORT"]), username)


    async def run(self) -> None:
        if (self._user is None):
            return

        await self._user.generateID()
        await self._user.connect()
        await self._user.receive()

        await choose_room(self._user)

        while True:
            try:
                await asyncio.gather(
                    self._user.receive(),
                    self._user.send()
                )

            except Exception as e:
                print('Error: {}'.format(e))
                break

            except KeyboardInterrupt:
                break

        self._user.disconnect()
