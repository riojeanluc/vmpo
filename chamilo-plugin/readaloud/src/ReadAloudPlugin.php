<?php
/* For licensing terms, see /license.txt */

/**
 * Plugin "Lecture à voix haute" (text-to-speech) pour Chamilo 1.11.x.
 *
 * La synthèse vocale est faite dans le navigateur via la Web Speech API
 * (window.speechSynthesis) : aucun service externe, aucune clé d'API,
 * aucune donnée envoyée hors de la plateforme.
 */
class ReadAloudPlugin extends Plugin
{
    const RATE_MIN = 0.5;
    const RATE_MAX = 2.0;

    protected function __construct()
    {
        parent::__construct(
            '1.0',
            'VMPO',
            [
                'tool_enable' => 'boolean',
                'show_for_anonymous' => 'boolean',
                'default_rate' => 'text',
                'content_selector' => 'text',
            ]
        );
    }

    /**
     * @return ReadAloudPlugin
     */
    public static function create()
    {
        static $result = null;

        return $result ? $result : $result = new self();
    }

    /**
     * Le widget doit-il être affiché pour l'utilisateur courant ?
     *
     * @return bool
     */
    public function isVisibleForCurrentUser()
    {
        if ('true' !== $this->get('tool_enable')) {
            return false;
        }

        $isAnonymous = api_is_anonymous() || 0 === (int) api_get_user_id();
        if ($isAnonymous && 'true' !== $this->get('show_for_anonymous')) {
            return false;
        }

        return true;
    }

    /**
     * Vitesse de lecture par défaut, bornée entre RATE_MIN et RATE_MAX.
     *
     * @return float
     */
    public function getDefaultRate()
    {
        $rate = (float) str_replace(',', '.', (string) $this->get('default_rate'));
        if ($rate <= 0) {
            return 1.0;
        }

        return max(self::RATE_MIN, min(self::RATE_MAX, $rate));
    }

    /**
     * Sélecteur CSS de la zone de contenu à lire (vide = détection automatique).
     *
     * @return string
     */
    public function getContentSelector()
    {
        return trim((string) $this->get('content_selector'));
    }

    /**
     * Code langue BCP 47 utilisé pour choisir la voix (ex. "fr", "en").
     *
     * @return string
     */
    public function getSpeechLanguage()
    {
        $iso = api_get_language_isocode();

        return !empty($iso) ? $iso : 'fr';
    }
}
