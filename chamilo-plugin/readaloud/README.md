# Plugin Chamilo « Lecture à voix haute » (readaloud)

Ajoute sur les pages de Chamilo LMS (1.11.x) un petit lecteur flottant
**Écouter / Pause / Arrêter / Vitesse** qui lit à voix haute :

- le **texte sélectionné** par l'utilisateur, s'il y en a un ;
- sinon la **zone de contenu principale** de la page (`#cm-content`), y compris
  le contenu des iframes de même origine (documents, parcours d'apprentissage).

La synthèse vocale utilise la **Web Speech API** du navigateur
(`window.speechSynthesis`) : gratuite, sans clé d'API, et aucune donnée
ne sort de la plateforme. La voix est choisie selon la langue de
l'utilisateur dans Chamilo.

## Installation

1. Copier le dossier `readaloud/` dans `<chamilo>/plugin/readaloud/`.
2. *Administration → Plugins* : cocher **Lecture à voix haute** puis
   *Activer les plugins sélectionnés*.
3. Cliquer sur **Configurer** : cocher *Activer la lecture à voix haute*
   et régler les options (vitesse par défaut, visiteurs anonymes,
   sélecteur CSS de la zone à lire).
4. *Administration → Régions* (bouton « Régions » de la page Plugins) :
   placer le plugin dans une région présente sur toutes les pages,
   par exemple **pre_footer** ou **footer_right**.

## Architecture

```
readaloud/
├── plugin.php              Déclaration du plugin (lu par Administration > Plugins)
├── index.php               Exécuté à chaque affichage de la région : prépare {{ readaloud.* }}
├── template.tpl            Gabarit Twig du widget (boutons + chargement JS/CSS)
├── src/ReadAloudPlugin.php Classe du plugin (extends Plugin) : réglages et règles d'affichage
├── lang/french.php         Traductions (titre, réglages, libellés)
├── lang/english.php
└── resources/
    ├── js/readaloud.js     Extraction du texte + lecture (Web Speech API)
    └── css/readaloud.css   Style du lecteur flottant
```

Fonctionnement :

1. `PluginManager::loadRegion()` inclut `index.php`, qui remplit `$_template`
   (langue, vitesse, libellés traduits, URL des ressources) puis affiche
   `template.tpl`.
2. Le gabarit insère le widget (masqué par défaut) et `readaloud.js`.
3. Le script vérifie que le navigateur gère la synthèse vocale, affiche le
   widget, puis au clic :
   - récupère le texte visible (sans menus, scripts, éléments masqués,
     ni éléments marqués `data-readaloud-ignore`) ;
   - le découpe en phrases de 200 caractères max. (contourne la coupure des
     longs énoncés dans Chrome et permet la reprise précise) ;
   - lit les morceaux les uns après les autres.

Accessibilité : vrais `<button>`, focus visible, annonce via `aria-live`,
touche **Échap** pour arrêter, vitesse mémorisée par navigateur.

## Limites et évolutions possibles

- La qualité et le choix des voix dépendent du navigateur/système
  (très bonnes sous Chrome, Edge, Safari ; plus limitées sous Linux).
- Les contenus SCORM hébergés sur un autre domaine (iframe d'une autre
  origine) ne peuvent pas être lus par le navigateur.
- Pour des voix identiques partout, on peut remplacer la Web Speech API par
  un service de synthèse côté serveur (Google Cloud TTS, Azure, Amazon Polly,
  ou Piper auto-hébergé) : ajouter un point d'entrée `ajax.php` dans le plugin
  qui reçoit le texte, appelle le service et renvoie un fichier audio
  (mis en cache), puis le lire avec un élément `<audio>`.
- Surlignage du passage en cours de lecture (évènement `onboundary`).
- Chamilo 2.x (Symfony/Vue) utilise une autre architecture de plugins :
  ce code correspond à la branche 1.11.x.
