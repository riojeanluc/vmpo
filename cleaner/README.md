# cleaner_app

Outil CLI de nettoyage pour **Windows** : fichiers temporaires, Corbeille,
historique et cache des navigateurs (Chrome, Edge, Brave, Firefox).

Écrit en Python (bibliothèque standard uniquement, aucune dépendance
d'exécution). `pytest` est utilisé pour les tests.

## Principes de sécurité

- **Simulation par défaut.** `clean` n'affiche que ce qui *serait* supprimé
  tant que `--yes` n'est pas passé explicitement.
- **Âge minimum** sur les fichiers temporaires (3 jours par défaut, réglable
  via `--min-age-days`) pour ne pas toucher des fichiers qu'un programme est
  en train d'écrire.
- **Suppression individuelle avec gestion d'erreur** : un fichier verrouillé
  (navigateur ouvert, antivirus, etc.) est simplement ignoré et reporté,
  jamais une cause de plantage.
- **Historique Firefox** : les entrées liées à un signet sont préservées,
  seul l'historique de navigation est effacé.
- Tout ce qui est réellement supprimé est journalisé (`--log-file`).

## Utilisation

```bash
# Analyse (aucune suppression)
python -m cleaner_app scan

# Sortie JSON (pour intégration/scripting)
python -m cleaner_app scan-json

# Simulation de nettoyage (par défaut, rien n'est supprimé)
python -m cleaner_app clean

# Nettoyage réel
python -m cleaner_app clean --yes

# Limiter aux catégories, changer l'âge minimum des temporaires, journaliser
python -m cleaner_app --categories system --min-age-days 7 --log-file cleaner.log clean --yes
```

## Ce qui est nettoyé

| Catégorie | Cible | Action |
|---|---|---|
| `system` | `%TEMP%`, `%TMP%`, `C:\Windows\Temp` | suppression des fichiers plus vieux que `--min-age-days` |
| `system` | Corbeille Windows | vidage complet |
| `browser` | Historique Chrome/Edge/Brave (`History` SQLite) | suppression des lignes `urls`/`visits` |
| `browser` | Historique Firefox (`places.sqlite`) | suppression de l'historique, signets préservés |
| `browser` | Cache Chrome/Edge/Brave/Firefox | suppression du contenu du dossier de cache |

Portée volontairement limitée pour la v1 : cookies, mots de passe enregistrés
et téléchargements ne sont pas touchés.

## Obtenir un .exe (sans installer Python)

Un exécutable Windows autonome (`cleaner_app.exe`) est construit
automatiquement par la CI GitHub Actions (`.github/workflows/build-windows-exe.yml`,
runner `windows-latest`, via PyInstaller) à chaque push touchant `cleaner/`.
Le binaire est disponible en téléchargement dans l'onglet **Actions** du
dépôt, sur le run correspondant, section *Artifacts* (`cleaner_app-windows-exe`).

Pour le lancer sans passer par un terminal, il suffit ensuite de copier
`cleaner_app.exe` où l'on veut sur le disque et d'exécuter, par exemple :

```
cleaner_app.exe scan
cleaner_app.exe clean --yes
```

Pour builder soi-même sur une machine Windows :

```bash
cd cleaner
pip install pyinstaller
pyinstaller --onefile --name cleaner_app --console run_cleaner.py
# résultat dans dist/cleaner_app.exe
```

## Développement

```bash
pip install pytest
python -m pytest
```

La structure sépare volontairement *scan* (lecture seule, calcule ce qui est
récupérable) de *clean* (écriture), pour permettre validation/confirmation
avant toute suppression. Les appels spécifiques à Windows (Corbeille,
`tasklist`) sont isolés dans `platform_utils.py` et les scanners, gardés
derrière `is_windows()`, afin que le reste du code reste testable sur toute
plateforme.
