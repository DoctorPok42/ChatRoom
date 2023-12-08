import os
import asyncio
from dotenv import load_dotenv
from argparse import ArgumentParser

from engine import Engine

parser = ArgumentParser()
parser.add_argument("-p", "--port", action="store", help="Port du serveur", type=int)
parser.add_argument("-a", "--address", action="store", help="Adresse du serveur", type=str)

args = parser.parse_args()

load_dotenv()

config = {
    "SERVER_HOST": os.getenv("SERVER_HOST"),
    "SERVER_PORT": os.getenv("SERVER_PORT"),
}

if (config["SERVER_HOST"] == None):
    if (args.address == None):
        config["SERVER_HOST"] = "localhost"
        config["SERVER_PORT"] = 8080
    else:
        config["SERVER_HOST"] = args.address
        config["SERVER_PORT"] = args.port


if __name__ == '__main__':
    username = input('Enter your username: ')

    while (username == '' or len(username) < 2):
        username = input('\033cEnter your username: ')


    engine = Engine(config, username)
    asyncio.run(engine.run())
