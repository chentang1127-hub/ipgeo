/**
 * IPGeo Language Selector — custom UI powered by Google Translate.
 *
 * All pages stay English by default. When a visitor selects a different
 * language, Google Translate handles the translation in-page.
 * Choice is persisted via cookie (googtrans) so it survives page reloads.
 *
 * Supported languages: EN (default), 中文, 日本語, Español, Português, Deutsch, Français
 *
 * The language buttons are embedded as static HTML on every page so they
 * render immediately. This script enhances them with click handlers,
 * active-state tracking, and Google Translate integration.
 */
(function () {
  'use strict';

  // ── Language definitions ─────────────────────────────────────────
  var LANGS = [
    { code: 'en', name: 'English',     flag: '🇺🇸' },
    { code: 'zh-CN', name: '中文',       flag: '🇨🇳' },
    { code: 'ja', name: '日本語',       flag: '🇯🇵' },
    { code: 'es', name: 'Español',      flag: '🇪🇸' },
    { code: 'pt', name: 'Português',    flag: '🇧🇷' },
    { code: 'de', name: 'Deutsch',      flag: '🇩🇪' },
    { code: 'fr', name: 'Français',     flag: '🇫🇷' },
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

  // ── Google Translate integration ──────────────────────────────────
  var googleReady = false;
  var pendingLang = null;

  function setGoogleTranslate(langCode) {
    if (langCode === 'en') {
      // Restore to English: clear the cookie and remove the translate bar
      document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;';
      // Reload to clear Google's DOM mutations
      if (document.querySelector('.goog-te-banner-frame') || document.querySelector('font')) {
        window.location.reload();
      }
      return;
    }

    // Set the googtrans cookie
    document.cookie = 'googtrans=/en/' + langCode + '; path=/';

    if (googleReady) {
      // If Google Translate is already loaded, just reload
      window.location.reload();
    } else {
      // Load Google Translate script if not already loaded
      pendingLang = langCode;
      loadGoogleTranslate();
    }
  }

  function loadGoogleTranslate() {
    if (document.getElementById('google-translate-script')) return;

    // Add a hidden div that Google Translate needs
    var el = document.createElement('div');
    el.id = 'google_translate_element';
    el.style.display = 'none';
    document.body.appendChild(el);

    // Google Translate init callback
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

    // Load the script
    var script = document.createElement('script');
    script.id = 'google-translate-script';
    script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    document.head.appendChild(script);
  }

  // ── Set language ──────────────────────────────────────────────────
  function setLang(langCode) {
    current = langCode;
    localStorage.setItem('ipgeo_lang', langCode);
    updateActiveButton();
    document.documentElement.lang = langCode;

    if (langCode !== 'en') {
      setGoogleTranslate(langCode);
    } else {
      setGoogleTranslate('en');
    }
  }

  // ── Enhance static HTML buttons ───────────────────────────────────
  function injectStyles() {
    if (document.getElementById('i18n-styles')) return;
    var style = document.createElement('style');
    style.id = 'i18n-styles';
    style.textContent =
      '#lang-selector { display: inline-flex; align-items: center; gap: 2px; flex-shrink: 0; }' +
      '#lang-selector .lang-sep { color: var(--border, #252530); font-size: .7rem; user-select: none; margin: 0 1px; }' +
      '#lang-selector .lang-link { background: none; border: none; color: var(--dim, #71717a); cursor: pointer; font-size: .75rem; font-family: inherit; padding: 3px 6px; border-radius: 4px; transition: all .15s; text-decoration: none; white-space: nowrap; }' +
      '#lang-selector .lang-link:hover { color: var(--text, #e4e4e7); background: var(--card, #13131a); }' +
      '#lang-selector .lang-link.active { color: var(--accent, #7c3aed); font-weight: 600; }';
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
      '.goog-text-highlight { background: none !important; box-shadow: none !important; }';
    document.head.appendChild(hideCss);
  }

  function buildButtonHTML(lang) {
    var cls = lang.code === current ? ' active' : '';
    return '<button class="lang-link' + cls + '" data-lang="' + lang.code + '">' + lang.name + '</button>';
  }

  function enhanceSelector() {
    var container = document.getElementById('lang-selector');
    if (!container) return;

    injectStyles();
    injectGtHider();

    // Check if buttons already exist (from static HTML)
    var existing = container.querySelectorAll('[data-lang]');

    if (existing.length === 0) {
      // Fallback: build buttons from scratch
      var html = '';
      for (var i = 0; i < LANGS.length; i++) {
        if (i > 0) html += '<span class="lang-sep">|</span>';
        html += buildButtonHTML(LANGS[i]);
      }
      container.innerHTML = html;
    }

    // Add click handlers to all buttons
    container.querySelectorAll('[data-lang]').forEach(function (b) {
      b.addEventListener('click', function () {
        var lang = this.getAttribute('data-lang');
        if (lang !== current) {
          setLang(lang);
        }
      });
    });

    updateActiveButton();
  }

  function updateActiveButton() {
    var container = document.getElementById('lang-selector');
    if (!container) return;
    container.querySelectorAll('[data-lang]').forEach(function (b) {
      var isActive = b.getAttribute('data-lang') === current;
      b.classList.toggle('active', isActive);
    });
  }

  // ── Bootstrap ────────────────────────────────────────────────────
  function init() {
    document.documentElement.lang = current;

    // If a non-English language was stored, load Google Translate
    if (current !== 'en') {
      loadGoogleTranslate();
    }

    function mount() {
      if (document.getElementById('lang-selector')) {
        enhanceSelector();
      }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mount);
    } else {
      mount();
    }
  }

  init();
})();
