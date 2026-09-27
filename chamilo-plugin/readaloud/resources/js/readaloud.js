/* For licensing terms, see /license.txt */
/**
 * Lecture à voix haute pour Chamilo — synthèse vocale côté navigateur
 * (Web Speech API). Lit le texte sélectionné s'il y en a un, sinon la zone
 * de contenu principale de la page (y compris les iframes de même origine,
 * utilisées par les parcours d'apprentissage et les documents).
 */
(function () {
    'use strict';

    var widget = document.getElementById('readaloud-widget');
    if (!widget) {
        return;
    }
    if (!('speechSynthesis' in window) || typeof window.SpeechSynthesisUtterance !== 'function') {
        // Navigateur non compatible : on laisse le widget masqué.
        return;
    }

    var synth = window.speechSynthesis;
    var cfg = widget.dataset;
    var playBtn = widget.querySelector('[data-action="play"]');
    var stopBtn = widget.querySelector('[data-action="stop"]');
    var rateSelect = widget.querySelector('[data-action="rate"]');
    var status = widget.querySelector('[data-role="status"]');
    var playIcon = playBtn.querySelector('.readaloud-icon');
    var playText = playBtn.querySelector('.readaloud-text');

    var DEFAULT_SELECTORS = ['#cm-content', '.page-content', '#content', 'main', '[role="main"]', 'body'];
    var SKIP_SELECTOR = 'script, style, noscript, template, svg, nav, header, footer, select, ' +
        '[aria-hidden="true"], [hidden], [data-readaloud-ignore], #readaloud-widget, ' +
        '.navbar, .breadcrumb, .actions, .toolbar, #toolbar, .sr-only';
    var BLOCK_TAGS = /^(ADDRESS|ARTICLE|ASIDE|BLOCKQUOTE|BR|DD|DIV|DL|DT|FIELDSET|FIGCAPTION|FIGURE|FORM|H[1-6]|HR|LI|MAIN|OL|P|PRE|SECTION|TABLE|TD|TH|TR|UL)$/;
    var MAX_CHUNK = 200;
    var STORAGE_KEY = 'readaloud.rate';

    var state = 'idle'; // idle | playing | paused
    var chunks = [];
    var index = 0;
    var session = 0; // incrémenté à chaque arrêt pour ignorer les évènements obsolètes
    var voice = null;

    // ---------------------------------------------------------------- voix

    function pickVoice() {
        var lang = (cfg.lang || document.documentElement.lang || 'fr').toLowerCase();
        var base = lang.split(/[-_]/)[0];
        var voices = synth.getVoices();
        var exact = null;
        var partial = null;
        for (var i = 0; i < voices.length; i++) {
            var vLang = (voices[i].lang || '').toLowerCase().replace('_', '-');
            if (vLang === lang) {
                exact = exact || voices[i];
            } else if (vLang.split('-')[0] === base) {
                // On privilégie la voix locale/par défaut quand il y en a plusieurs.
                if (!partial || voices[i].localService || voices[i]['default']) {
                    partial = partial && partial.localService ? partial : voices[i];
                }
            }
        }
        voice = exact || partial;
    }

    pickVoice();
    if (typeof synth.addEventListener === 'function') {
        synth.addEventListener('voiceschanged', pickVoice);
    } else {
        synth.onvoiceschanged = pickVoice;
    }

    // ---------------------------------------------------------------- vitesse

    function readStoredRate() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            return null;
        }
    }

    function storeRate(value) {
        try {
            window.localStorage.setItem(STORAGE_KEY, value);
        } catch (e) {
            // Stockage indisponible (navigation privée…) : sans importance.
        }
    }

    function selectRate(value) {
        var wanted = parseFloat(value);
        if (isNaN(wanted)) {
            return;
        }
        var best = rateSelect.options[0];
        for (var i = 0; i < rateSelect.options.length; i++) {
            var opt = rateSelect.options[i];
            if (Math.abs(parseFloat(opt.value) - wanted) < Math.abs(parseFloat(best.value) - wanted)) {
                best = opt;
            }
        }
        rateSelect.value = best.value;
    }

    selectRate(readStoredRate() || cfg.rate || '1');

    // ---------------------------------------------------------------- extraction du texte

    function isVisible(el) {
        var view = el.ownerDocument.defaultView;
        if (!view) {
            return false;
        }
        var style = view.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden' && el.getClientRects().length > 0;
    }

    function blockAncestor(node, root) {
        var el = node.parentNode;
        while (el && el !== root && !BLOCK_TAGS.test(el.nodeName)) {
            el = el.parentNode;
        }
        return el;
    }

    function collectText(root, parts) {
        var doc = root.ownerDocument || root;
        var walker = doc.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
            acceptNode: function (node) {
                if (node.nodeType === 1) {
                    if (node.matches(SKIP_SELECTOR) || !isVisible(node)) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_SKIP;
                }
                return /\S/.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
            }
        });
        var lastBlock = null;
        var node;
        while ((node = walker.nextNode())) {
            var block = blockAncestor(node, root);
            if (block !== lastBlock) {
                parts.push('\n');
                lastBlock = block;
            }
            parts.push(node.nodeValue);
        }

        // Contenus affichés dans des iframes de même origine (parcours, documents).
        var frames = root.querySelectorAll('iframe, frame');
        for (var i = 0; i < frames.length; i++) {
            try {
                var body = frames[i].contentDocument && frames[i].contentDocument.body;
                if (body && isVisible(frames[i])) {
                    parts.push('\n');
                    collectText(body, parts);
                }
            } catch (e) {
                // iframe d'une autre origine : inaccessible, on l'ignore.
            }
        }
    }

    function findContentRoot() {
        var selectors = cfg.selector ? [cfg.selector].concat(DEFAULT_SELECTORS) : DEFAULT_SELECTORS;
        for (var i = 0; i < selectors.length; i++) {
            var el = null;
            try {
                el = document.querySelector(selectors[i]);
            } catch (e) {
                // Sélecteur invalide saisi par l'administrateur.
            }
            if (el) {
                return el;
            }
        }
        return document.body;
    }

    function getTextToRead() {
        var selection = window.getSelection ? String(window.getSelection()).trim() : '';
        if (selection) {
            return selection;
        }
        var parts = [];
        collectText(findContentRoot(), parts);
        return parts.join('');
    }

    /**
     * Découpe le texte en morceaux courts : Chrome interrompt les énoncés
     * trop longs (~15 s), et cela permet un arrêt/reprise plus précis.
     */
    function splitText(text) {
        var sentences = text
            .replace(/[ \t ]+/g, ' ')
            .split(/\n+|(?<=[.!?…;:])\s+/)
            .map(function (s) { return s.trim(); })
            .filter(function (s) { return /[\p{L}\p{N}]/u.test(s); });

        var result = [];
        sentences.forEach(function (sentence) {
            while (sentence.length > MAX_CHUNK) {
                var cut = sentence.lastIndexOf(' ', MAX_CHUNK);
                if (cut < MAX_CHUNK / 2) {
                    cut = MAX_CHUNK;
                }
                result.push(sentence.slice(0, cut));
                sentence = sentence.slice(cut).trim();
            }
            if (sentence) {
                result.push(sentence);
            }
        });
        return result;
    }

    // ---------------------------------------------------------------- lecture

    function setState(newState) {
        state = newState;
        widget.classList.toggle('is-playing', state === 'playing');
        widget.classList.toggle('is-paused', state === 'paused');
        stopBtn.disabled = state === 'idle';

        if (state === 'playing') {
            playIcon.innerHTML = '&#10074;&#10074;';
            playText.textContent = cfg.labelPause;
        } else if (state === 'paused') {
            playIcon.innerHTML = '&#9654;';
            playText.textContent = cfg.labelResume;
        } else {
            playIcon.innerHTML = '&#9654;';
            playText.textContent = cfg.labelPlay;
        }
        playBtn.setAttribute('aria-pressed', state === 'playing' ? 'true' : 'false');
    }

    function announce(message) {
        status.textContent = '';
        window.setTimeout(function () { status.textContent = message; }, 50);
    }

    function speakNext(currentSession) {
        if (currentSession !== session) {
            return;
        }
        if (index >= chunks.length) {
            stop();
            return;
        }
        var utterance = new SpeechSynthesisUtterance(chunks[index]);
        utterance.lang = voice ? voice.lang : (cfg.lang || 'fr');
        if (voice) {
            utterance.voice = voice;
        }
        utterance.rate = parseFloat(rateSelect.value) || 1;
        utterance.onend = function () {
            if (currentSession === session) {
                index++;
                speakNext(currentSession);
            }
        };
        utterance.onerror = function (event) {
            if (currentSession === session && event.error !== 'interrupted' && event.error !== 'canceled') {
                index++;
                speakNext(currentSession);
            }
        };
        synth.speak(utterance);
    }

    function start() {
        chunks = splitText(getTextToRead());
        if (!chunks.length) {
            announce(cfg.labelNothing);
            return;
        }
        synth.cancel();
        session++;
        index = 0;
        setState('playing');
        speakNext(session);
    }

    function stop() {
        session++;
        synth.cancel();
        chunks = [];
        index = 0;
        setState('idle');
    }

    function restartCurrentChunk() {
        // Relance le morceau courant (après changement de vitesse ou reprise).
        session++;
        synth.cancel();
        setState('playing');
        speakNext(session);
    }

    playBtn.addEventListener('click', function () {
        if (state === 'idle') {
            start();
        } else if (state === 'playing') {
            synth.pause();
            setState('paused');
        } else {
            // Certains navigateurs (Android, Firefox) gèrent mal resume() :
            // on reprend au début du morceau courant, ce qui est plus fiable.
            restartCurrentChunk();
        }
    });

    stopBtn.addEventListener('click', stop);

    rateSelect.addEventListener('change', function () {
        storeRate(rateSelect.value);
        if (state === 'playing') {
            restartCurrentChunk();
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && state !== 'idle') {
            stop();
        }
    });

    // Évite qu'une lecture continue après avoir quitté la page.
    window.addEventListener('pagehide', stop);

    setState('idle');
    widget.hidden = false;
})();
