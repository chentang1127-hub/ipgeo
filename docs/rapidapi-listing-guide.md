# RapidAPI Listing 配置手册

> 对照 RapidAPI Provider Dashboard 每个输入框，逐一写好。上线时复制粘贴即可。

---

## 1. Listing 基本信息

| 字段 | 内容 |
|------|------|
| **API Name** | `IPGeo` |
| **API Title** (显示在搜索结果) | `IPGeo — IP Geolocation API with Built-in Security Detection` |
| **Subtitle** (标题下方一行) | `VPN/proxy/Tor/hosting detection included, MaxMind-powered, free 10K lookups/mo` |
| **Category** | `Data` → `IP Geolocation` 或 `Geolocation` |
| **Website** | `https://getipgeo.com` |
| **Support Email** | `support@getipgeo.com` |
| **Terms of Service URL** | `https://getipgeo.com/terms` |
| **Privacy Policy URL** | `https://getipgeo.com/privacy` |

---

## 2. About / Description（产品介绍）

> 在 Dashboard → Listing → **About** 区块填写，支持 Markdown。

```
## Accurate IP geolocation. Security tags included. Free 10K/month.

IPGeo gives you country, city, coordinates, ISP, ASN, timezone plus
security flags (VPN, proxy, Tor, hosting) — all on the Free plan.

### What you get on EVERY plan (including Free):

| Feature | IPGeo Free | Typical Free Tier |
|---------|-----------|-------------------|
| City accuracy | ✅ country/city/coordinates | varies (often degraded on free) |
| Security detection | ✅ VPN / proxy / Tor / hosting | ❌ or paid add-on |
| Free lookups/month | **10,000** | 100–3,000 |
| Rate limit | 60/min | 30/min |
| Batch endpoint | ✅ up to 100 IPs | ❌ or limited |
| Data engine | **MaxMind** (same as Cloudflare, npm) | various |

### Response grouped by use case — not 30 flat fields:

```json
{
  "ip": "8.8.8.8",
  "location": {
    "country": {"code": "US", "name": "United States"},
    "city": "Mountain View",
    "latitude": 37.4223,
    "longitude": -122.0842,
    "accuracy_km": 10,
    "timezone": "America/Los_Angeles"
  },
  "network": {
    "isp": "Google LLC",
    "asn": 15169,
    "type": "hosting"
  },
  "security": {
    "is_tor": false,
    "is_vpn": false,
    "is_proxy": false,
    "is_hosting": true
  },
  "meta": {
    "data_source": "MaxMind"
  }
}
```

### Works great for:

🌍 **Geo-targeted advertising** — country/city/coordinates for ad targeting
🛡️ **Fraud detection** — flag hosting, Tor, proxy IPs before processing payments
📊 **Analytics** — segment users by geography, ISP, network type
🔐 **Access control** — block or challenge traffic from VPNs and data centers
🌐 **Content localization** — timezone, country, language detection

### Built for developers:

- `curl` one-liner works out of the box
- Zero-migration upgrades — same key, same URL, same JSON structure
- `/v1/health` public endpoint — check status without auth
- Ask questions — we reply in <2 hours
```

---

## 3. Tags（搜索关键词）

```
ip-geolocation
ip-lookup
geoip
ip-api
geolocation
ip-to-location
asn-lookup
ip-data
vpn-detection
proxy-detection
tor-detection
ip-city-lookup
batch-ip-lookup
ip-address-lookup
free-ip-geolocation
```

---

## 4. Plans & Pricing 配置

> 在 Dashboard → **Plans & Pricing** 依次创建。RapidAPI 支持按 API 端点区分配额（但初期只用全局配额最简单）：

### Plan 1: FREE

| 字段 | 值 |
|------|-----|
| **Plan Name** | `FREE` |
| **Monthly Price** | `$0.00` |
| **Hard Limit** | `10000` requests/month |
| **Overages** | ❌ Disabled（超了直接拒绝，不扣费） |
| **Rate Limit** | `60` requests/minute |
| **Description** | `10,000 lookups/month — MaxMind-powered geolocation with VPN/proxy/Tor detection included. Perfect for prototyping and small projects.` |

### Plan 2: STARTER

| 字段 | 值 |
|------|-----|
| **Plan Name** | `STARTER` |
| **Monthly Price** | `$9.00` |
| **Hard Limit** | `100000` requests/month |
| **Overages** | ❌ Disabled |
| **Rate Limit** | `600` requests/minute |
| **Description** | `100K lookups/month — higher rate limits for production apps. Full geolocation + security flags included.` |

### Plan 3: PRO

| 字段 | 值 |
|------|-----|
| **Plan Name** | `PRO` |
| **Monthly Price** | `$29.00` |
| **Hard Limit** | `500000` requests/month |
| **Overages** | ❌ Disabled |
| **Rate Limit** | `3000` requests/minute |
| **Description** | `500K lookups/month — highest rate limits for growing teams. Full geolocation + security flags. Priority email support included.` |

### Plan 4: BUSINESS

| 字段 | 值 |
|------|-----|
| **Plan Name** | `BUSINESS` |
| **Monthly Price** | `$79.00` |
| **Hard Limit** | `1000000` requests/month |
| **Overages** | ❌ Disabled |
| **Rate Limit** | `10000` requests/minute |
| **Description** | `1M lookups/month — for high-traffic platforms. Full geolocation + security flags. SLA included.` |

### Plan 5: ENTERPRISE

| 字段 | 值 |
|------|-----|
| **Plan Name** | `ENTERPRISE` |
| **Monthly Price** | `Custom`（设 $199 起点，备注 "Contact for custom pricing"） |
| **Hard Limit** | `Unlimited` |
| **Overages** | N/A |
| **Rate Limit** | `Unlimited` |
| **Description** | `Unlimited lookups + risk scoring. Private deployment option, custom SLA, dedicated support. Contact support@getipgeo.com.` |

---

## 5. RapidAPI Subscription Mapping 对照

> Dashboard 里创建的 Plan Name 必须和中间件的 `SUBSCRIPTION_PLAN_MAP` 一致：

| RapidAPI Dashboard Plan | 中间件 Key | 映射到 IPGeo Plan |
|------------------------|-----------|------------------|
| `FREE` | `FREE` | `free` |
| `STARTER` | `BASIC` | `starter` → **注意：Dashboard 叫 STARTER，但 RapidAPI 的订阅头里叫 BASIC！** |
| `PRO` | `PRO` | `pro` |
| `BUSINESS` | `ULTRA` | `business` → **Dashboard 叫 BUSINESS，但 RapidAPI 头里叫 ULTRA！** |
| `ENTERPRISE` | `MEGA` | `enterprise` |

> ⚠️ **重要：** RapidAPI 的 Plan Name（自定义）和 X-RapidAPI-Subscription 头里的值（RapidAPI 定死：FREE/BASIC/PRO/ULTRA/MEGA/ENTERPRISE）是两套命名。中间件已经按 RapidAPI 标准名映射好了。在 Dashboard 创建 Plan 时 Plan Name 用左边列的名字，X-RapidAPI-Subscription 会是右边第二列——中间件自动处理。

---

## 6. Logo & Branding

| 项目 | 规格 | 说明 |
|------|------|------|
| **Logo** | 500×500px PNG | 建议暗色背景 + IPGeo 字标。如果没有现成的，先用简单的文字 Logo |
| **Banner** | 1500×500px PNG | 可选，搜索结果里的横幅 |
| **Favicon** | 使用现有网站的 |

---

## 7. 常见问题 (FAQ)

> 在 Questions 区预写，上线后第一时间发布：

**Q: What data source does IPGeo use?**
> We use MaxMind databases (the same engine trusted by Cloudflare, npm, and Cisco). Every plan gets the same data — we don't downgrade free users to a weaker database. City accuracy varies by country and IP type (broadband vs mobile), as with all IP geolocation providers.

**Q: What happens when I hit the monthly quota?**
> Requests return HTTP 429 with a clear error message. We never auto-charge your card for overages. Upgrade to a higher plan when you need more.

**Q: How is the security data sourced?**
> Tor exit nodes from check.torproject.org (refreshed hourly). Hosting detection via ASN heuristics (major cloud providers tracked). Proxy detection from MaxMind database traits. VPN detection coming soon.

**Q: Can I change my plan later and keep the same API key?**
> Yes. Plans are tied to your RapidAPI subscription — upgrade/downgrade in RapidAPI and your key keeps working. No code changes needed.

**Q: Do you log or store IP addresses?**
> No. IPs are looked up in-memory and never written to persistent storage. We log aggregate request counts only.

**Q: What's the latency?**
> Typically <1ms for database lookups (mmap-backed local database). Total response time including network: 10–50ms depending on your location. We're hosted in the US.

**Q: How often is the database updated?**
> We refresh the MaxMind database regularly. Tor exit list refreshes hourly.

**Q: Do you support IPv6?**
> Yes — both IPv4 and IPv6 lookups work on all endpoints.

---

## 8. 上线日 Checklist

上线前逐项确认：

- [ ] GeoLite2-City.mmdb 和 GeoLite2-ASN.mmdb 已上传 VPS
- [ ] `IPGEO_RAPIDAPI_ENABLED=true` 已设
- [ ] `IPGEO_RAPIDAPI_PROXY_SECRET` 已从 Dashboard 复制
- [ ] `docker compose up -d --build` 已重启
- [ ] Dashboard 测试控制台：FREE 计划调用成功
- [ ] Dashboard 测试控制台：PRO 计划调用成功，响应里 `meta.data_source: "MaxMind"`
- [ ] 字段映射验证：`?fields=country,network` 正确返回 location + network 块
- [ ] Usage 端点正常返回配额信息
- [ ] Health 端点公开可访问，不需鉴权
- [ ] FAQ 已预写好（上线后立即发到 Questions 区）
- [ ] Logo 已上传
- [ ] Plans & Pricing 五个计划全部创建
- [ ] 提交审核
