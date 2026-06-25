# IPGeo 产品+渠道全面审计

> 2026-06-25 | 运营总监视角

---

## 一、产品能力清单（逐项验证）

### 核心 API

| 功能 | 状态 | 技术实现 | 实测 |
|------|------|---------|------|
| IP → 国家/大洲 | ✅ | MaxMind GeoLite2 MMDB | `{"country":{"code":"US","name":"United States"}}` |
| IP → 城市 | ⚠️ | GeoLite2 ~37% 城市填充 | `"city": null` 常见 |
| IP → 经纬度 | ⚠️ | GeoLite2 粗略坐标 | `accuracy_km: 1000`（低精度） |
| IP → 时区 | ✅ | GeoLite2 | `"timezone":"America/Chicago"` |
| IP → ISP | ✅ | GeoLite2 ASN DB | `"isp":"Cloudflare, Inc."` |
| IP → ASN | ✅ | GeoLite2 ASN DB | `"asn": 13335` |
| 自己的 IP 查询 | ✅ | `/v1/ip/me` | 读 CF-Connecting-IP |
| 批量查询 | ✅ | POST `/v1/ip/batch`，最多 100 IP | 并发线程池 |
| 字段过滤 | ✅ | `?fields=country,security` | 按需返回 |
| 健康检查 | ✅ | `/v1/health`，无需认证 | 状态正常 |
| 用量查询 | ✅ | `/v1/usage` | 返回配额/已用/剩余 |

### 安全检测（核心差异化）

| 检测 | 状态 | 数据来源 | 实测 |
|------|------|---------|------|
| Tor 出口节点 | ✅ | torproject.org，每小时更新 | 1255 个出口跟踪中 |
| VPN 检测 | ⚠️ | MaxMind GeoLite2 traits | `"is_vpn": false/true` |
| 代理检测 | ⚠️ | MaxMind GeoLite2 traits | `"is_proxy": false/true` |
| 托管机房检测 | ✅ | 自维护 ASN 列表（18 个云厂商） | `"is_hosting": true` |

> **注：VPN 和代理检测依赖 MaxMind 数据。Tor 和托管机房检测是自建，无需第三方。**

### 套餐体系

| 套餐 | 价格 | 月配额 | 速率限制 | Paddle 状态 |
|------|------|--------|---------|------------|
| Free | $0 | 10,000 | 60/min | — |
| Starter | $9 | 100,000 | 600/min | ✅ 已激活 |
| Pro | $29 | 500,000 | 3,000/min | ✅ 已激活 |
| Business | $79 | 1,000,000 | 10,000/min | ✅ 已激活 |
| Enterprise | 联系 | 无限 | 定制 | 手动 |

### 认证方式

| 方式 | 状态 |
|------|------|
| X-API-Key header | ✅ |
| ?api_key= URL 参数 | ✅ |
| X-RapidAPI-Key（RapidAPI 代理） | ✅ |

### SDK

| 语言 | 包管理器 | 安装命令 | 状态 |
|------|---------|---------|------|
| Python | PyPI | `pip install ipgeo-api` | ✅ 已发布 |
| JavaScript | npm | `npm install ipgeo-api` | ✅ 已发布 |

### 网站页面

| 页面 | URL | 状态 |
|------|-----|------|
| 首页（含 Live Demo） | `/` | ✅ |
| 注册/付费 | `/signup` | ✅ Paddle 已激活 |
| 手动升级（PayPal 兜底）| `/manual-upgrade` | ✅ |
| 注册成功 | `/success` | ✅ |
| 定价页 | `/pricing` | ✅ |
| API 文档 | `api.getipgeo.com/docs` | ✅ Swagger |
| IP 查询工具 | `/ip-lookup` | ✅ |
| 我的 IP 工具 | `/my-ip` | ✅ |
| ASN 查询工具 | `/asn-lookup` | ✅ |
| IP 到城市 | `/ip-to-city` | ✅ |
| IP 到国家 | `/ip-to-country` | ✅ |
| 博客 | `/blog` | ✅ 2 篇 |
| 系统状态 | `/status` | ✅ |
| 路线图 | `/roadmap` | ✅ |
| 更新日志 | `/changelog` | ✅ |
| 公开统计 | `/public-stats` | ✅ |
| IPinfo 替代 | `/ipinfo-alternative` | ✅ |
| MaxMind 对比 | `/why-maxmind` | ✅ |
| 条款/隐私/退款 | `/terms` `/privacy` `/refund` | ✅ |

### 支付

| 支付方式 | 状态 | 限制 |
|---------|------|------|
| Paddle（信用卡/PayPal 等）| ✅ 今天激活 | 月付 ≥$100 才打款 |
| PayPal.Me（手动） | ✅ 备用 | `paypal.me/getipgeo` |

---

## 二、渠道覆盖全图（每个渠道的实际状态）

### 已建立的渠道

| 渠道 | 链接/标识 | 当前数据 | 效果评级 |
|------|---------|---------|---------|
| **PyPI** | [pypi.org/project/ipgeo-api](https://pypi.org/project/ipgeo-api) | v0.1.0，0 下载 | 就绪，无流量 |
| **npm** | [npmjs.com/package/ipgeo-api](https://www.npmjs.com/package/ipgeo-api) | v0.1.0，0 下载 | 就绪，无流量 |
| **RapidAPI** | [rapidapi.com/chentang1127/api/ipgeo11](https://rapidapi.com/chentang1127/api/ipgeo11) | 1 subscriber, 1.9/10 pop | 就绪，无人用 |
| **GitHub** | [github.com/chentang1127-hub/ipgeo](https://github.com/chentang1127-hub/ipgeo) | 0 Star, 0 Fork | 存在但无社交证明 |
| **GitHub (Python SDK)** | [github.com/chentang1127-hub/ipgeo-python](https://github.com/chentang1127-hub/ipgeo-python) | 0 Star | 存在但无本地 git 历史 |
| **GitHub (JS SDK)** | [github.com/chentang1127-hub/ipgeo-js](https://github.com/chentang1127-hub/ipgeo-js) | 0 Star | 存在但无本地 git 历史 |
| **public-apis** | [PR #6347](https://github.com/public-apis/public-apis/pull/6347) | 待 merge | 预期 50-200 UV/周 |
| **首页 SEO** | `getipgeo.com` | 基础 meta 标签 | Google 基本未收录 |
| **博客 SEO** | `getipgeo.com/blog` | 1 篇文章 | 等收录 |
| **PayPal.Me** | `paypal.me/getipgeo` | 已创建 | 备用支付 |

### 未覆盖的渠道（按重要性排序）

| 渠道 | 重要性 | 为什么重要 | 当前进展 |
|------|--------|---------|---------|
| **Stack Overflow** | 🔴🔴🔴 | IPinfo 靠这个做到 400 亿请求/月 | 零 |
| **Reddit** | 🔴🔴🔴 | 开发者社区，长尾 SEO 持续数年 | 零 |
| **Dev.to** | 🔴🔴 | 开发者写作社区，文章会被 Google 收录 | 零 |
| **GitHub 社交证明** | 🔴🔴 | 0 Star 的仓库没人敢用 | 需初始化 git |
| **API 目录** | 🟡🟡 | apilist.fun, publicapis.io, freepublicapis.com | 零 |
| **HN Show** | 🟡🟡 | 需有基础社交证明才能发 | 条件未就绪 |
| **Product Hunt** | 🟡 | 浪费时间如果没基础 | 暂不做 |
| **国内社区** | 🟡🟡 | CSDN/掘金/V2EX/知乎 | 零 |
| **邮件列表** | 🟢 | Mailchimp 免费版 | 零 |
| **YouTube** | 🟢 | 教程视频，长尾流量 | 零 |
| **Twitter/X** | 🟢 | 开发者社群 | 无账号 |

---

## 三、我们的真实差异化（竞品没有的）

### 一句话定位

> **"唯一一个在免费套餐里包含 VPN/代理/Tor 检测的 IP 定位 API。"**

### 核对竞品

| 功能 | IPGeo Free | ipinfo Free | ip-api Free | ipstack Free |
|------|-----------|------------|------------|-------------|
| 免费配额 | 10K/月 | 50K/月 | 无上限（非商用） | 100/月 |
| VPN 检测 | ✅ 免费 | ❌ | ❌ | ❌ |
| 代理检测 | ✅ 免费 | ❌ | ❌ | ❌ |
| Tor 检测 | ✅ 免费 | ❌ | ❌ | ❌ |
| 托管机房 | ✅ 免费 | ❌ | ❌ | ❌ |
| 需要注册 | ✅ 是 | 否 | 否 | 否 |
| HTTPS | ✅ | ✅ | ✅ | ❌ 免费无 |
| Python SDK | ✅ | 有（官方） | 无 | 无 |
| JS SDK | ✅ | 有（官方） | 无 | 无 |
| 起步价格 | **$9/月** | $99/月 | $15/月 | $14.99/月 |

### 弱点（诚实的）

| 弱点 | 严重度 | 说明 |
|------|--------|------|
| 城市精度差 | 🔴 | GeoLite2 ~37%，city 经常 null |
| 品牌为 0 | 🔴 | 没人听说过 |
| GitHub 0 Star | 🟡 | 社交证明缺失 |
| 数据源合规待确认 | 🟡 | GeoLite 商业授权等 MaxMind 回复 |
| 无 ASN/Company 数据 | 🟡 | 竞品 ipinfo 有 |
| 新域名 | 🟡 | Google 信任低，收录慢 |

---

## 四、转化漏斗（现状 + 目标）

```
现状：
  曝光 0 → 访问 0 → 注册 0 → 付费 0

30 天目标：
  曝光 5000 → 访问 500 (10%) → 注册 50 (10%) → 付费 1 (2%)
  
  渠道来源：
  Stack Overflow: 30%
  Reddit: 20%  
  SEO: 20%
  SDK (PyPI/npm): 15%
  直接/其他: 15%
```

---

## 五、核心结论

**我们能卖的东西：**
1. 同价位唯一含安全检测的 IP API
2. 价格是 ipinfo 的 1/10
3. Python + JS SDK 即装即用
4. 免费 10K/月

**我们现在缺的：**
1. 开发者不知道我们存在 ← **这是唯一的瓶颈**
2. Stack Overflow / Reddit 零存在 ← **最高杠杆的修复**
3. GitHub 0 Star ← **社交证明死循环**

**不紧急的事（别分散精力）：**
- 数据源精度 ← 等 MaxMind 回复，不影响推流
- 首页优化 ← 首页够好了
- Product Hunt ← 现在发是浪费
- Google 广告 ← 先验证免费渠道

---

*此文档是活文档，随项目进展更新。*
