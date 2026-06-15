/**
 * IPGeo Language Selector — dropdown UI powered by Google Translate.
 *
 * All pages stay English by default. When a visitor selects a different
 * language, Google Translate handles the translation in-page.
 * Choice is persisted via cookie (googtrans) so it survives page reloads.
 *
 * Supported languages: EN, 中文, 日本語, Español, Português, Deutsch, Français
 */
(function () {
  'use strict';

  // ── Language definitions ─────────────────────────────────────────
  var LANGS = [
    { code: 'en', name: 'English',     flag: '🇺🇸', short: 'EN' },
    { code: 'zh-CN', name: '中文',       flag: '🇨🇳', short: '中文' },
    { code: 'ja', name: '日本語',       flag: '🇯🇵', short: '日本語' },
    { code: 'es', name: 'Español',      flag: '🇪🇸', short: 'ES' },
    { code: 'pt', name: 'Português',    flag: '🇧🇷', short: 'PT' },
    { code: 'de', name: 'Deutsch',      flag: '🇩🇪', short: 'DE' },
    { code: 'fr', name: 'Français',     flag: '🇫🇷', short: 'FR' },
  ];

  var DEFAULT = 'en';

  // ── Read current language ─────────────────────────────────────────
  function getCurrent() {
    // 1. Check our localStorage first
    var stored = localStorage.getItem('ipgeo_lang');
    if (stored) return stored;

    // 2. Check Google's googtrans cookie
    var match = document.cookie.match(/(?:^|;\s*)googtrans=\/en\/([^;]+)/);
    if (match) {
      var code = decodeURIComponent(match[1]);
      for (var i = 0; i < LANGS.length; i++) {
        if (LANGS[i].code === code || LANGS[i].code.split('-')[0] === code) {
          return LANGS[i].code;
        }
      }
    }

    // 3. Detect browser language
    try {
      var browser = (navigator.language || '').split('-')[0].toLowerCase();
      for (var j = 0; j < LANGS.length; j++) {
        if (LANGS[j].code === browser || LANGS[j].code.split('-')[0] === browser) {
          if (LANGS[j].code !== 'en') return LANGS[j].code;
          break;
        }
      }
    } catch (e) {}

    return DEFAULT;
  }

  var current = getCurrent();

  function getLangDef(code) {
    for (var i = 0; i < LANGS.length; i++) {
      if (LANGS[i].code === code) return LANGS[i];
    }
    return LANGS[0];
  }

  // ── Google Translate integration ──────────────────────────────────
  var googleReady = false;
  var pendingLang = null;

  function setGoogleTranslate(langCode) {
    if (langCode === 'en') {
      document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
      if (document.querySelector('.goog-te-banner-frame') || document.querySelector('font')) {
        window.location.reload();
      }
      return;
    }

    document.cookie = 'googtrans=/en/' + langCode + '; path=/';

    if (googleReady) {
      window.location.reload();
    } else {
      pendingLang = langCode;
      loadGoogleTranslate();
    }
  }

  function loadGoogleTranslate() {
    if (document.getElementById('google-translate-script')) return;

    var el = document.createElement('div');
    el.id = 'google_translate_element';
    el.style.display = 'none';
    document.body.appendChild(el);

    window.googleTranslateElementInit = function () {
      new google.translate.TranslateElement(
        {
          pageLanguage: 'en',
          includedLanguages: 'zh-CN,ja,es,pt,de,fr',
          layout: google.translate.TranslateElement.InlineLayout.HORIZONTAL,
          autoDisplay: false,
        },
        'google_translate_element'
      );
      googleReady = true;
      if (pendingLang) {
        document.cookie = 'googtrans=/en/' + pendingLang + '; path=/';
        window.location.reload();
      }
    };

    var script = document.createElement('script');
    script.id = 'google-translate-script';
    script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    document.head.appendChild(script);
  }

  // ── Set language ──────────────────────────────────────────────────
  function setLang(langCode) {
    current = langCode;
    localStorage.setItem('ipgeo_lang', langCode);
    document.documentElement.lang = langCode;

    // Update toggle button label + dropdown active state
    updateUI();

    if (langCode !== 'en') {
      setGoogleTranslate(langCode);
    } else {
      setGoogleTranslate('en');
    }
  }

  // ── Dropdown selector ─────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('i18n-styles')) return;
    var style = document.createElement('style');
    style.id = 'i18n-styles';
    style.textContent =
      /* Toggle button */
      '#lang-selector { position: relative; display: inline-flex; flex-shrink: 0; }' +
      '#lang-selector .lang-toggle {' +
      '  display: flex; align-items: center; gap: 4px;' +
      '  background: var(--card, #13131a); border: 1px solid var(--border, #252530);' +
      '  color: var(--dim, #71717a); cursor: pointer;' +
      '  font-size: .75rem; font-family: inherit;' +
      '  padding: 5px 10px; border-radius: 6px;' +
      '  transition: all .15s; white-space: nowrap;' +
      '}' +
      '#lang-selector .lang-toggle:hover {' +
      '  color: var(--text, #e4e4e7); border-color: var(--dim2, #52525b);' +
      '}' +
      '#lang-selector .lang-toggle .lang-arrow {' +
      '  font-size: .6rem; transition: transform .15s;' +
      '}' +
      '#lang-selector.open .lang-toggle .lang-arrow {' +
      '  transform: rotate(180deg);' +
      '}' +
      '#lang-selector.open .lang-toggle {' +
      '  color: var(--text, #e4e4e7); border-color: var(--accent, #7c3aed);' +
      '}' +
      /* Dropdown menu */
      '#lang-selector .lang-menu {' +
      '  display: none; position: absolute; top: 100%; right: 0;' +
      '  margin-top: 6px; background: var(--card, #13131a);' +
      '  border: 1px solid var(--border, #252530);' +
      '  border-radius: 8px; min-width: 150px;' +
      '  box-shadow: 0 8px 24px rgba(0,0,0,0.4);' +
      '  z-index: 100; overflow: hidden;' +
      '}' +
      '#lang-selector.open .lang-menu { display: block; }' +
      /* Menu items */
      '#lang-selector .lang-option {' +
      '  display: block; width: 100%; text-align: left;' +
      '  background: none; border: none;' +
      '  color: var(--dim, #71717a); cursor: pointer;' +
      '  font-size: .78rem; font-family: inherit;' +
      '  padding: 8px 14px;' +
      '  transition: all .1s; white-space: nowrap;' +
      '}' +
      '#lang-selector .lang-option:hover {' +
      '  color: var(--text, #e4e4e7); background: rgba(255,255,255,0.04);' +
      '}' +
      '#lang-selector .lang-option.active {' +
      '  color: var(--accent, #7c3aed); font-weight: 600;' +
      '  background: rgba(124,58,237,0.08);' +
      '}' +
      /* Divider between options */;
    document.head.appendChild(style);
  }

  function injectGtHider() {
    if (document.getElementById('gt-auto-hide')) return;
    var hideCss = document.createElement('style');
    hideCss.id = 'gt-auto-hide';
    hideCss.textContent =
      'body { top: 0 !important; }' +
      '.goog-te-banner-frame { display: none !important; }' +
      '.skiptranslate { display: none !important; }' +
      '#goog-gt-tt { display: none !important; }' +
      '.goog-tooltip { display: none !important; }' +
      '.goog-tooltip:hover { display: none !important; }' +
      '.goog-text-highlight { background: none !important; box-shadow: none !important; }' +
      '#google_translate_element { display: none !important; }' +
      'iframe.goog-te-menu-frame { display: none !important; }';
    document.head.appendChild(hideCss);
  }

  function buildDropdown() {
    var container = document.getElementById('lang-selector');
    if (!container) return;

    var cur = getLangDef(current);
    var optionsHTML = '';
    for (var i = 0; i < LANGS.length; i++) {
      var cls = LANGS[i].code === current ? ' active' : '';
      optionsHTML += '<button class="lang-option' + cls + '" data-lang="' + LANGS[i].code + '">' +
        LANGS[i].flag + ' ' + LANGS[i].name + '</button>';
    }

    container.innerHTML =
      '<button class="lang-toggle">' +
        '<span class="lang-label">' + cur.flag + ' ' + cur.short + '</span>' +
        '<span class="lang-arrow">▾</span>' +
      '</button>' +
      '<div class="lang-menu">' + optionsHTML + '</div>';
  }

  function updateUI() {
    var container = document.getElementById('lang-selector');
    if (!container) return;

    var cur = getLangDef(current);

    // Update toggle label
    var label = container.querySelector('.lang-label');
    if (label) label.textContent = cur.flag + ' ' + cur.short;

    // Update active option
    container.querySelectorAll('.lang-option').forEach(function (opt) {
      var isActive = opt.getAttribute('data-lang') === current;
      opt.classList.toggle('active', isActive);
    });
  }

  function setupEvents() {
    var container = document.getElementById('lang-selector');
    if (!container) return;

    // Toggle dropdown
    var toggle = container.querySelector('.lang-toggle');
    if (toggle) {
      toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        container.classList.toggle('open');
      });
    }

    // Option clicks
    container.querySelectorAll('.lang-option').forEach(function (opt) {
      opt.addEventListener('click', function (e) {
        e.stopPropagation();
        var lang = this.getAttribute('data-lang');
        if (lang !== current) {
          setLang(lang);
        }
        container.classList.remove('open');
      });
    });
  }

  // Click outside to close
  document.addEventListener('click', function () {
    var container = document.getElementById('lang-selector');
    if (container) container.classList.remove('open');
  });

  // Escape key to close
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var container = document.getElementById('lang-selector');
      if (container) container.classList.remove('open');
    }
  });

  // ── Bootstrap ────────────────────────────────────────────────────
  function init() {
    document.documentElement.lang = current;

    // Only auto-translate if the user EXPLICITLY chose this language
    if (current !== 'en' && localStorage.getItem('ipgeo_lang')) {
      loadGoogleTranslate();
    }

    function mount() {
      var container = document.getElementById('lang-selector');
      if (!container) return;

      injectStyles();
      injectGtHider();
      buildDropdown();
      setupEvents();
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mount);
    } else {
      mount();
    }
  }

  init();
})();
