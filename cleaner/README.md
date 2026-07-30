# cleaner_app

Outil CLI de nettoyage pour **Windows** (fichiers temporaires, Corbeille,
historique et cache des navigateurs Chrome, Edge, Brave, Firefox) et pour un
**NAS Synology** joignable en SSH depuis le PC (caches de miniatures @eaDir,
corbeilles des dossiers partagés).

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
- **Synology** : authentification SSH par clé uniquement (`BatchMode=yes`,
  aucun mot de passe n'est jamais demandé ni stocké). Avant la première
  utilisation, connecte-toi une fois manuellement en SSH au NAS
  (`ssh user@nas`) pour accepter son empreinte — sans quoi la connexion
  échouera proprement plutôt que de risquer une interception silencieuse.

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

# NAS Synology (via SSH, clé privée recommandée)
python -m cleaner_app --categories synology --ssh-host nas.local --ssh-user admin ^
    --ssh-key C:\Users\moi\.ssh\id_ed25519 scan

python -m cleaner_app --categories synology --ssh-host nas.local --ssh-user admin ^
    --ssh-key C:\Users\moi\.ssh\id_ed25519 clean --yes
```

## Ce qui est nettoyé

| Catégorie | Cible | Action |
|---|---|---|
| `system` | `%TEMP%`, `%TMP%`, `C:\Windows\Temp` | suppression des fichiers plus vieux que `--min-age-days` |
| `system` | Corbeille Windows | vidage complet |
| `browser` | Historique Chrome/Edge/Brave (`History` SQLite) | suppression des lignes `urls`/`visits` |
| `browser` | Historique Firefox (`places.sqlite`) | suppression de l'historique, signets préservés |
| `browser` | Cache Chrome/Edge/Brave/Firefox | suppression du contenu du dossier de cache |
| `synology` | Caches de miniatures `@eaDir` | suppression complète du dossier (DSM le régénère à la demande) |
| `synology` | Corbeilles `#recycle` des dossiers partagés | suppression du contenu, le dossier `#recycle` est conservé |

Portée volontairement limitée pour la v1 : cookies, mots de passe enregistrés
et téléchargements ne sont pas touchés côté navigateurs ; côté Synology,
seuls `@eaDir` et `#recycle` sont couverts (pas de logs DSM, cache du Centre
de paquets, ni Docker/Container Manager).

La catégorie `synology` nécessite `--ssh-host` et `--ssh-user` (sinon
`cleaner_app` s'arrête avec un message d'erreur explicite). Par défaut, seul
`/volume1` est scanné ; utilise `--synology-volumes /volume1,/volume2` si le
NAS a plusieurs volumes.

## Obtenir un exécutable Windows (sans installer Python)

La CI GitHub Actions (`.github/workflows/build-windows-exe.yml`, runner
`windows-latest`) construit automatiquement, à chaque push touchant
`cleaner/` ou `installer/`, deux livrables disponibles en téléchargement
dans l'onglet **Actions** du dépôt (section *Artifacts* du run) :

- **`cleaner_app-windows-exe`** : le `.exe` portable seul (via PyInstaller).
  Il suffit de le copier où l'on veut sur le disque et de le lancer :
  ```
  cleaner_app.exe scan
  cleaner_app.exe clean --yes
  ```
- **`CleanerAppSetup`** : un vrai installeur Windows (`CleanerAppSetup.exe`,
  généré avec Inno Setup à partir de `installer/cleaner_app.iss`). Il propose
  un assistant d'installation classique, ajoute un raccourci « Analyser
  (scan) » et « Désinstaller » au menu Démarrer, et une entrée dans
  *Programmes et fonctionnalités*.

Pour builder soi-même sur une machine Windows :

```bash
# 1. le .exe portable
cd cleaner
pip install pyinstaller
pyinstaller --onefile --name cleaner_app --console run_cleaner.py
# résultat dans dist/cleaner_app.exe

# 2. l'installeur (nécessite Inno Setup : https://jrsoftware.org/isinfo.php)
cd ../installer
iscc cleaner_app.iss
# résultat dans installer/output/CleanerAppSetup.exe
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
