# Claudette - Chat LLM avec Tools

Un projet Python pour interagir avec des LLMs via Ollama avec support de tools (accès internet, opérations fichiers, exécution de commandes).

## Fonctionnalités

- Chat interactif avec des modèles Ollama
- Tools fonctionnels:
  - **Web Search**: Recherche sur internet
  - **File Read**: Lire des fichiers
  - **File Write**: Créer/écrire des fichiers
  - **File Edit**: Modifier des fichiers existants
  - **Command Execute**: Exécuter des commandes shell

## Installation

```bash
pip install -r requirements.txt
```

## Prérequis

- Python 3.8+
- Ollama installé et en cours d'exécution
- Un modèle compatible avec les function calls (ex: llama3.1, mistral, etc.)

## Utilisation

```bash
python main.py
```

## Configuration

Modifiez `config.json` pour:
- Changer le modèle Ollama
- Activer/désactiver certains tools
- Configurer les paramètres de sécurité

## Sécurité

Par défaut, l'exécution de commandes nécessite une confirmation. Vous pouvez désactiver cela dans la configuration (non recommandé).
