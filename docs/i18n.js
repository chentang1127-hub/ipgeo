/**
 * IPGeo i18n — lightweight translation system.
 * No framework, no build step.  ~4 KB.
 *
 * Usage:
 *   <span data-i18n="hero.title">Fortune-500 Accuracy</span>
 *
 * Add translations below, then the matching text is swapped at page load.
 * Falls back to the English text in the HTML when a key is missing.
 */
(function () {
  'use strict';

  // ── Supported languages ──────────────────────────────────────────
  var SUPPORTED = ['en', 'zh'];
  var DEFAULT = 'en';

  // ── Translation dictionaries ─────────────────────────────────────
  // Keys use dotted paths matching data-i18n attributes.
  var DICT = {
    en: {},  // English is the HTML source — no overrides needed
    zh: {
      // Nav
      'nav.features': '功能',
      'nav.demo': '演示',
      'nav.pricing': '定价',
      'nav.docs': '文档',
      'nav.signup': '免费注册',

      // Hero
      'hero.badge': 'IPinfo 的经济实惠替代方案',
      'hero.title': '世界500强级别精度，<span>创业公司友好价格</span>',
      'hero.free_callout': '每月 10,000 次免费请求。无需信用卡。',
      'hero.subtitle': 'MaxMind 级别的精准度，无需自己运维。行业标准 GeoIP2，一个 API 密钥，零基础设施。比 ipinfo 便宜 60%。',
      'hero.cta_free': '获取免费 API 密钥 →',
      'hero.cta_docs': 'API 文档',
      'hero.cta_demo': '在线演示 ↓',

      // Stats bar
      'stats.speed': '<0.3<span>ms</span>',
      'stats.speed_label': '平均响应时间',
      'stats.uptime': '99.9<span>%</span>',
      'stats.uptime_label': 'SLA 可用性目标',
      'stats.coverage': '200<span>+</span>',
      'stats.coverage_label': '覆盖国家和地区',

      // Trust signals
      'trust.datasource': 'MaxMind',
      'trust.datasource_label': 'GeoIP2 商业数据',
      'trust.updates': '每周',
      'trust.updates_label': '数据库更新',
      'trust.openapi': 'OpenAPI 3.1',
      'trust.openapi_label': '内置 Swagger 文档',
      'trust.cdn': 'Cloudflare',
      'trust.cdn_label': '全球 CDN 加速',

      // Trust bar
      'trustbar.status': '🟢 系统状态',
      'trustbar.roadmap': '📋 公开路线图',
      'trustbar.changelog': '📝 更新日志',
      'trustbar.stats': '📊 公开统计',

      // Why section
      'why.kicker': '为什么不直接用 MaxMind？',
      'why.title': '同样的数据，零运维负担',
      'why.subtitle': 'MaxMind GeoIP2 是行业金标准——但自己部署意味着 50 GB 下载、服务器配置和更新流水线。IPGeo 通过 REST API 提供同样的顶级数据。',
      'why.col_feature': '',
      'why.col_maxmind': '直接使用 MaxMind',
      'why.col_ipgeo': 'IPGeo',
      'why.row_setup': '数据库配置',
      'why.row_setup_maxmind': '下载 50+ GB，配置服务器',
      'why.row_setup_ipgeo': '✓ 无需配置 — 始终最新',
      'why.row_updates': '更新维护',
      'why.row_updates_maxmind': '每周手动更新流水线',
      'why.row_updates_ipgeo': '✓ 自动更新，零停机',
      'why.row_license': '商业授权',
      'why.row_license_maxmind': '需单独购买（$300+/年）',
      'why.row_license_ipgeo': '✓ 已包含在订阅中',
      'why.row_api': 'API 封装',
      'why.row_api_maxmind': '需自行构建 REST 层',
      'why.row_api_ipgeo': '✓ 开箱即用',
      'why.row_monitoring': '监控告警',
      'why.row_monitoring_maxmind': '需自行搭建',
      'why.row_monitoring_ipgeo': '✓ Prometheus + 公开状态页',

      // Features
      'features.kicker': '为什么选择 IPGeo',
      'features.title': '为开发者而生',
      'features.subtitle': 'IP 地理位置所需的全部功能，没有多余的。',
      'features.card1_title': '极简集成',
      'features.card1_body': '一行 curl，一个 X-API-Key 请求头。无需 OAuth 流程，无需 JWT，零仪式感。',
      'features.card2_title': '比 ipinfo 便宜 60%',
      'features.card2_body': 'Pro 套餐：50 万次查询仅 $29/月。ipinfo 同样数据要 $99/月。一样的数据，更低的价格。',
      'features.card3_title': '简单的 API Key 认证',
      'features.card3_body': '只需一个 X-API-Key 请求头。无 OAuth 流程，无 JWT 令牌，简洁直接。',
      'features.card4_title': '批量查询',
      'features.card4_body': '单次 POST 请求最多查询 100 个 IP。按 IP 数量计费，不多收。',
      'features.card5_title': '每周自动更新',
      'features.card5_body': '数据库每周自动更新。零停机，永远保持最新数据。',
      'features.card6_title': '零依赖开发模式',
      'features.card6_body': '无需 Redis 或 Docker 即可运行。一条命令启动本地开发环境。',

      // Use cases
      'usecases.kicker': '应用场景',
      'usecases.title': '将 IP 数据转化为商业决策',
      'usecases.subtitle': '开发者使用 IPGeo 提升收入、防止欺诈并优化用户体验。',
      'usecases.card1_title': '欺诈与安全',
      'usecases.card1_body': '在支付前标记高风险 IP，匹配 IP 国家与账单地址，封锁受制裁地区。减少拒付并执行地理围栏——一次 API 调用即可完成。',
      'usecases.card2_title': '内容本地化',
      'usecases.card2_body': '自动重定向到访客语言的页面，显示本地货币和价格，按国家限制内容。无需用户选择，自动匹配。',
      'usecases.card3_title': '数据分析与定位',
      'usecases.card3_body': '按城市、国家或 ISP 聚合流量。构建区域使用仪表板。在不收集 PII 的情况下了解用户位置分布。',

      // Live Demo
      'demo.kicker': '在线演示',
      'demo.title': '亲自试试',
      'demo.subtitle': '输入任意 IP 地址，即时查看 GeoIP2 返回的完整数据。无需注册。',
      'demo.placeholder': '输入 IP 地址，例如 8.8.8.8...',
      'demo.lookup_btn': '查询',
      'demo.result_title': '查询结果',
      'demo.raw_json': '原始 JSON',

      // Pricing
      'pricing.kicker': '定价',
      'pricing.title': '简单、透明的定价',
      'pricing.subtitle': '所有套餐包含相同的数据质量。按查询量选择。',
      'pricing.free': '免费',
      'pricing.free_quota': '10,000 次/月',
      'pricing.free_price': '$0',
      'pricing.free_cta': '免费注册',
      'pricing.starter': '入门',
      'pricing.starter_quota': '50,000 次/月',
      'pricing.starter_cta': '开始使用',
      'pricing.pro': '专业版',
      'pricing.pro_quota': '500,000 次/月',
      'pricing.pro_cta': '开始使用',
      'pricing.business': '商业版',
      'pricing.business_quota': '2,000,000 次/月',
      'pricing.business_cta': '开始使用',
      'pricing.enterprise': '企业版',
      'pricing.enterprise_quota': '定制',
      'pricing.enterprise_cta': '联系我们',
      'pricing.all_plans_include': '所有套餐包含：',
      'pricing.feature_maxmind': 'MaxMind GeoIP2 数据',
      'pricing.feature_sla': '99.9% SLA',
      'pricing.feature_api': 'RESTful API',
      'pricing.feature_batch': '批量查询（100 IPs）',
      'pricing.feature_ssl': '256-bit SSL 加密',
      'pricing.feature_support': '邮件技术支持',

      // CTA
      'cta.title': '准备好开始了？',
      'cta.subtitle': '每月 10,000 次免费查询。无需信用卡，无需承诺。',
      'cta.button': '免费获取 API 密钥 →',

      // Footer
      'footer.product': '产品',
      'footer.resources': '资源',
      'footer.legal': '法律',
      'footer.signup': '注册',
      'footer.api_docs': 'API 文档',
      'footer.vs_maxmind': 'IPGeo vs MaxMind',
      'footer.ipinfo_alt': 'IPinfo 替代方案',
      'footer.ip_lookup': 'IP 查询',
      'footer.my_ip': '我的 IP',
      'footer.asn_lookup': 'ASN 查询',
      'footer.public_stats': '公开统计',
      'footer.status': '系统状态',
      'footer.roadmap': '路线图',
      'footer.changelog': '更新日志',
      'footer.license_guide': 'MaxMind 授权指南',
      'footer.terms': '服务条款',
      'footer.privacy': '隐私政策',
      'footer.refund': '退款政策',
      'footer.copyright': '© 2026 IPGeo. 基于 FastAPI + Redis 构建.',
    }
  };

  // ── State ────────────────────────────────────────────────────────
  var current = localStorage.getItem('ipgeo_lang') || detectLang();

  function detectLang() {
    try {
      var lang = (navigator.language || '').slice(0, 2).toLowerCase();
      return SUPPORTED.indexOf(lang) !== -1 ? lang : DEFAULT;
    } catch (e) {
      return DEFAULT;
    }
  }

  // ── Translate the page ───────────────────────────────────────────
  function translate(lang) {
    if (lang === 'en') {
      // Revert to original English text stored in data-i18n-orig
      document.querySelectorAll('[data-i18n]').forEach(function (el) {
        var orig = el.getAttribute('data-i18n-orig');
        if (orig !== null) {
          el.innerHTML = orig;
        }
      });
      // Also revert placeholder and value attributes
      document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
        el.placeholder = el.getAttribute('data-i18n-placeholder-orig') || '';
      });
      document.querySelectorAll('[data-i18n-value]').forEach(function (el) {
        el.value = el.getAttribute('data-i18n-value-orig') || '';
      });
      document.querySelectorAll('[data-i18n-href]').forEach(function (el) {
        el.href = el.getAttribute('data-i18n-href-orig') || '';
      });
      return;
    }

    var dict = DICT[lang] || {};
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      // On first run, store the original English text
      if (el.getAttribute('data-i18n-orig') === null) {
        el.setAttribute('data-i18n-orig', el.innerHTML);
      }
      if (dict[key]) {
        el.innerHTML = dict[key];
      }
    });
    // Translate placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      if (el.getAttribute('data-i18n-placeholder-orig') === null) {
        el.setAttribute('data-i18n-placeholder-orig', el.placeholder);
      }
      if (dict[key]) {
        el.placeholder = dict[key];
      }
    });
    // Translate values (for inputs)
    document.querySelectorAll('[data-i18n-value]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-value');
      if (el.getAttribute('data-i18n-value-orig') === null) {
        el.setAttribute('data-i18n-value-orig', el.value);
      }
      if (dict[key]) {
        el.value = dict[key];
      }
    });
    // Translate hrefs (for links that point to language-specific pages)
    document.querySelectorAll('[data-i18n-href]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-href');
      if (el.getAttribute('data-i18n-href-orig') === null) {
        el.setAttribute('data-i18n-href-orig', el.href);
      }
      if (dict[key]) {
        el.href = dict[key];
      }
    });
  }

  function setLang(lang) {
    current = lang;
    localStorage.setItem('ipgeo_lang', lang);
    translate(lang);
    updateSelectorUI();
    document.documentElement.lang = lang;
  }

  // ── Language Selector UI ─────────────────────────────────────────
  var NAME_MAP = { en: 'English', zh: '中文' };
  var FLAG_MAP = { en: '🇺🇸', zh: '🇨🇳' };

  function buildSelector() {
    var container = document.getElementById('lang-selector');
    if (!container) return;

    // Inject minimal styles if not already present
    if (!document.getElementById('i18n-styles')) {
      var style = document.createElement('style');
      style.id = 'i18n-styles';
      style.textContent =
        '.lang-sel { position: relative; display: inline-block; }' +
        '.lang-sel-btn { display: flex; align-items: center; gap: 6px; background: transparent; border: 1px solid var(--border, #252530); color: var(--dim, #71717a); padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: .8rem; font-family: inherit; transition: all .2s; }' +
        '.lang-sel-btn:hover { border-color: var(--accent, #7c3aed); color: var(--text, #e4e4e7); }' +
        '.lang-sel-btn .arrow { font-size: .6rem; transition: transform .2s; }' +
        '.lang-sel.open .lang-sel-btn .arrow { transform: rotate(180deg); }' +
        '.lang-sel-dropdown { position: absolute; right: 0; top: calc(100% + 6px); background: var(--card, #13131a); border: 1px solid var(--border, #252530); border-radius: 8px; min-width: 140px; padding: 4px; display: none; z-index: 100; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }' +
        '.lang-sel.open .lang-sel-dropdown { display: block; }' +
        '.lang-sel-dropdown button { display: flex; align-items: center; gap: 8px; width: 100%; padding: 8px 12px; border: none; background: transparent; color: var(--dim, #71717a); cursor: pointer; font-size: .8rem; font-family: inherit; border-radius: 4px; text-align: left; transition: all .15s; }' +
        '.lang-sel-dropdown button:hover { background: var(--card2, #18181f); color: var(--text, #e4e4e7); }' +
        '.lang-sel-dropdown button.active { color: var(--accent, #7c3aed); font-weight: 600; background: rgba(124,58,237,0.08); }' +
        '.lang-sel-dropdown button .more-note { font-size: .65rem; color: var(--dim2, #52525b); margin-left: auto; }';
      document.head.appendChild(style);
    }

    var active = current;
    var activeName = NAME_MAP[active] || active.toUpperCase();
    var activeFlag = FLAG_MAP[active] || '';

    var html = '<div class="lang-sel" id="lang-sel-instance">';
    html += '<button class="lang-sel-btn" id="lang-sel-btn">' + activeFlag + ' ' + activeName + ' <span class="arrow">▾</span></button>';
    html += '<div class="lang-sel-dropdown">';
    SUPPORTED.forEach(function (code) {
      var cls = code === active ? ' active' : '';
      html += '<button class="' + cls + '" data-lang="' + code + '">' + (FLAG_MAP[code] || '') + ' ' + NAME_MAP[code] + '</button>';
    });
    // Add a separator + "More languages" item that triggers Google Translate
    html += '<hr style="border:none;border-top:1px solid var(--border,#252530);margin:4px 8px;">';
    html += '<button data-lang="google" style="font-size:.75rem;">🌐 More languages <span class="more-note">Google 翻译</span></button>';
    html += '</div></div>';

    container.innerHTML = html;

    // Event: toggle dropdown
    var inst = document.getElementById('lang-sel-instance');
    var btn = document.getElementById('lang-sel-btn');
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      inst.classList.toggle('open');
    });

    // Event: close dropdown on outside click
    document.addEventListener('click', function () {
      inst.classList.remove('open');
    });

    // Event: language selection
    inst.querySelectorAll('[data-lang]').forEach(function (b) {
      b.addEventListener('click', function () {
        var lang = this.getAttribute('data-lang');
        if (lang === 'google') {
          // Redirect through Google Translate
          var targetLang = prompt('Enter language code (e.g., ja, de, fr, es, pt, ko):', 'ja');
          if (targetLang) {
            var url = 'https://translate.google.com/translate?sl=en&tl=' + encodeURIComponent(targetLang) + '&u=' + encodeURIComponent(window.location.href);
            window.open(url, '_blank');
          }
        } else {
          setLang(lang);
        }
        inst.classList.remove('open');
      });
    });
  }

  function updateSelectorUI() {
    var inst = document.getElementById('lang-sel-instance');
    if (!inst) return;
    var active = current;
    var btn = document.getElementById('lang-sel-btn');
    if (btn) {
      btn.innerHTML = (FLAG_MAP[active] || '') + ' ' + NAME_MAP[active] + ' <span class="arrow">▾</span>';
    }
    inst.querySelectorAll('[data-lang]').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === active);
    });
  }

  // ── Bootstrap ────────────────────────────────────────────────────
  function init() {
    // Set lang attribute on <html>
    document.documentElement.lang = current;

    // Apply translations if not English
    if (current !== 'en') {
      // Wait for DOM to be ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
          translate(current);
        });
      } else {
        translate(current);
      }
    }

    // Build selector when DOM is ready
    function mount() {
      if (document.getElementById('lang-selector')) {
        buildSelector();
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
