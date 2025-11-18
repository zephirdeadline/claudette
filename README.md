# Claudette - Assistant de recherche avec Ollama

Claudette est un assistant de recherche qui utilise Ollama pour interagir avec des modèles de langage locaux. Il permet de rechercher des informations dans des documents et de générer des réponses contextuelles.

## Fonctionnalités

- Recherche de documents dans un répertoire spécifié
- Utilisation de modèles de langage locaux via Ollama
- Génération de réponses contextuelles basées sur les documents trouvés
- Interface en ligne de commande simple et intuitive
- Gestion des conversations avec historique

## Installation

1. Clonez le dépôt :
   ```bash
   git clone <repository-url>
   cd claudette
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Assurez-vous que Ollama est installé et en cours d'exécution :
   ```bash
   ollama --version
   ```

## Utilisation

### Ligne de commande

Pour lancer l'assistant :
```bash
python main.py
```

### Configuration

Le fichier `user.jsonl` contient les préférences de l'utilisateur. Vous pouvez le modifier pour personnaliser le comportement de l'assistant.

### Exemple d'utilisation

```bash
python main.py
> Quel est le but de ce projet ?
> Quels sont les avantages de l'IA ?
```

## Structure du projet

- `main.py` : Point d'entrée de l'application
- `src/` : Code source de l'assistant
- `build/` : Dossier de construction
- `dist/` : Dossier de distribution
- `requirements.txt` : Dépendances Python
- `claudette.spec` : Configuration pour PyInstaller
- `user.jsonl` : Configuration utilisateur

## Conventions de code

- Utilisation de Python 3.8+
- Suivi des conventions PEP 8
- Documentation avec docstrings
- Gestion des erreurs appropriée
- Tests unitaires dans le dossier `tests/`

## Licence

Ce projet est sous licence MIT.