{% if readaloud.show %}
<link rel="stylesheet" href="{{ readaloud.css_url }}">
<div id="readaloud-widget"
     class="readaloud-widget"
     role="region"
     aria-label="{{ readaloud.label_region|e('html_attr') }}"
     data-lang="{{ readaloud.lang|e('html_attr') }}"
     data-rate="{{ readaloud.rate|e('html_attr') }}"
     data-selector="{{ readaloud.selector|e('html_attr') }}"
     data-label-play="{{ readaloud.label_play|e('html_attr') }}"
     data-label-pause="{{ readaloud.label_pause|e('html_attr') }}"
     data-label-resume="{{ readaloud.label_resume|e('html_attr') }}"
     data-label-nothing="{{ readaloud.label_nothing|e('html_attr') }}"
     hidden>
    <button type="button" class="readaloud-btn readaloud-play" data-action="play">
        <span class="readaloud-icon" aria-hidden="true">&#9654;</span>
        <span class="readaloud-text">{{ readaloud.label_play }}</span>
    </button>
    <button type="button" class="readaloud-btn readaloud-stop" data-action="stop"
            aria-label="{{ readaloud.label_stop|e('html_attr') }}" title="{{ readaloud.label_stop|e('html_attr') }}" disabled>
        <span class="readaloud-icon" aria-hidden="true">&#9632;</span>
    </button>
    <label class="readaloud-rate">
        <span class="readaloud-sr-only">{{ readaloud.label_rate }}</span>
        <select data-action="rate" title="{{ readaloud.label_rate|e('html_attr') }}">
            <option value="0.75">0.75×</option>
            <option value="1">1×</option>
            <option value="1.25">1.25×</option>
            <option value="1.5">1.5×</option>
            <option value="2">2×</option>
        </select>
    </label>
    <span class="readaloud-sr-only" aria-live="polite" data-role="status"></span>
</div>
<script src="{{ readaloud.js_url }}" defer></script>
{% endif %}
