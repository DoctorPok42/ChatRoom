# ChatRoom

## Description

Petite application de chat en ligne, permettant de discuter avec plusieurs personnes en même temps.

## Installation

1. Cloner le projet
2. Installer les dépendances avec la commande

```bash
pip install -r requirements.txt
```

## Utilisation

1. Crée un fichier .env à la racine du projet
2. Ajouter les variables d'environnement suivantes

```bash
SERVER_HOST= # Adresse IP du serveur
SERVER_PORT= # Port du serveur
```

3. Lancer le serveur avec la commande

```bash
python .\server\server.py
```

4. Lancer le client avec la commande

```bash
python .\src\main.py
```

## Commandes

- `/exit` : Quitter le chat
- `/p <pseudo> <message>` : Envoyer un message privé à un utilisateur
- `@<pseudo>` : Mentionner un utilisateur
- `@everyone` : Mentionner tout le monde

## License

MIT
