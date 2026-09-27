<?php
/* For licensing terms, see /license.txt */

/**
 * Inclus par PluginManager::loadRegion() à chaque affichage d'une page
 * contenant la région choisie pour le plugin. Prépare les variables
 * disponibles dans template.tpl sous le nom {{ readaloud.* }}.
 */
require_once __DIR__.'/src/ReadAloudPlugin.php';

$plugin = ReadAloudPlugin::create();
$webPath = api_get_path(WEB_PLUGIN_PATH).'readaloud/resources/';

$_template['show'] = $plugin->isVisibleForCurrentUser();
$_template['lang'] = $plugin->getSpeechLanguage();
$_template['rate'] = $plugin->getDefaultRate();
$_template['selector'] = $plugin->getContentSelector();
$_template['css_url'] = $webPath.'css/readaloud.css?v='.$plugin->get_version();
$_template['js_url'] = $webPath.'js/readaloud.js?v='.$plugin->get_version();

$_template['label_region'] = $plugin->get_lang('WidgetLabel');
$_template['label_play'] = $plugin->get_lang('Listen');
$_template['label_pause'] = $plugin->get_lang('Pause');
$_template['label_resume'] = $plugin->get_lang('Resume');
$_template['label_stop'] = $plugin->get_lang('Stop');
$_template['label_rate'] = $plugin->get_lang('Speed');
$_template['label_nothing'] = $plugin->get_lang('NothingToRead');
