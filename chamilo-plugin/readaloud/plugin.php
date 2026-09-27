<?php
/* For licensing terms, see /license.txt */

/**
 * Déclaration du plugin, lue par Chamilo dans Administration > Plugins.
 */
require_once __DIR__.'/src/ReadAloudPlugin.php';

$plugin_info = ReadAloudPlugin::create()->get_info();

// Gabarit Twig affiché dans la région où l'administrateur place le plugin.
$plugin_info['templates'] = ['template.tpl'];
