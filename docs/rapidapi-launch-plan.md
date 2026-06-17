# IPGeo RapidAPI 上线计划书

> 文档版本: v2.0 | 日期: 2026-06-17 | 作者: 唐高生
>
> **v2.0 更新说明**：基于深度竞品分析和开发者画像研究，全面调整产品策略：
> - 所有计划统一使用 GeoIP2（告别 GeoLite2 试用不准问题）
> - 安全标签全计划免费（对着 natkapral 打）
> - 新增 IPGeo Risk 风险评分引擎（蓝海变现）
> - 定位从"最快"调整为"准确+安全"

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [RapidAPI 平台概况](#2-rapidapi-平台概况)
3. [竞品深度分析](#3-竞品深度分析)
4. [IPGeo 核心竞争力](#4-ipgeo-核心竞争力)
5. [定价策略](#5-定价策略)
6. [API 产品设计](#6-api-产品设计)
7. [技术实施方案](#7-技术实施方案)
8. [营销推广计划](#8-营销推广计划)
9. [时间线与里程碑](#9-时间线与里程碑)
10. [费用预算](#10-费用预算)
11. [风险与应对](#11-风险与应对)
12. [附录](#12-附录)

---

## 1. 执行摘要

### 1.1 目标

将 IPGeo 作为独立 API 产品上线 RapidAPI marketplace，在 Paddle 直售渠道之外开辟第二收入来源。RapidAPI 拥有 **4000 万+ 注册开发者**和 **4 万+ API 产品**，是 IP 地理定位 API 的高流量分发渠道。

### 1.2 核心判断

**RapidAPI 和 Paddle 直售不冲突，是互补关系：**

| 维度 | Paddle 直售 (getipgeo.com) | RapidAPI |
|------|--------------------------|----------|
| 获客来源 | 搜索引擎、口碑、主动推广 | 平台内搜索 + 推荐流量 |
| 客户类型 | 直接签约的长约客户 | 开发者自选、按需订阅 |
| 分成比例 | 5% + $0.50/笔 | 20% 平台佣金 |
| 品牌控制 | 完整品牌体验 | 平台统一界面 |
| 审核门槛 | 域名审核（当前卡住） | 技术审核，通常 2-5 天 |
| 上手难度 | 需要自己做支付、注册、管理后台 | 平台已提供全套基础设施 |

**结论：RapidAPI 先上，同时等 Paddle 审核。两个渠道共享同一套后端，产品升级一次，两端同步。**

### 1.3 IPGeo 的定位

**产品策略：红海引流 + 蓝海变现**

> **红海（IPGeo Location）** — 准确、安全、免费的 IP 地理定位 API
> - 全计划 GeoIP2（95%+ 城市准确率）
> - VPN/代理/Tor 检测免费包含
> - 10,000 次/月免费，足够完整项目开发

> **蓝海（IPGeo Risk）** — RapidAPI 上首个可解释的 IP 风险评分引擎
> - 风险评分 0-100 + 置信度 + 可解释的 verdict
> - 滥用情报（AbuseIPDB）+ IP 类型识别
> - 同一个 Key，零迁移成本

**不是"又一个 IP API"。** 是开发者在 RapidAPI 上能找到的**最准确（GeoIP2）+ 最安全（检测免费）+ 唯一可解释风险评分**的 IP 数据平台。

---

## 2. RapidAPI 平台概况

### 2.1 平台数据

| 指标 | 数据 |
|------|------|
| 注册开发者 | 4000 万+ |
| API 产品数 | 40,000+ |
| 平台佣金 | **20%**（所有付费计划） |
| 支付方式 | 信用卡（平台代收） |
| API Key 管理 | 平台自动生成 + 分发 |
| 限流 | 平台提供基础限流 |
| 文档自动生成 | OpenAPI Spec → 交互式文档 |
| 代码片段 | 自动生成 Node.js / Python / PHP / curl 等 |

### 2.2 RapidAPI 开发者用户画像

RapidAPI 上的开发者关注以下因素（按优先级排序，基于大量评论和评分分析）：

| 优先级 | 关注点 | 说明 | IPGeo 如何满足 |
|--------|--------|------|---------------|
| **1** | 数据准确度 | 试用第一秒查自己 IP，城市对不对 | GeoIP2 全计划，95%+ |
| **2** | 接入成本 | 5 分钟内能跑通第一个请求吗 | curl 一行可复制，零认知负担 |
| **3** | 价格可预期 | 免费够不够做 PoC？超了是拒绝还是自动扣？ | 10K/月免费，超了拒绝不扣费 |
| **4** | 可靠性 | 过去宕过几次？有没有 status page | Prometheus 监控，健康检查公开 |
| **5** | 安全/隐私 | 用户 IP 会不会被记录/转卖？HTTPS？ | 不记录 IP，256-bit SSL |
| **6** | 社区响应 | Questions 区回复速度 | 目标 <2h 响应 |
| **7** | 额外字段 | 安全检测、货币、时区等 | 安全标签免费，Risk Pro+ |

**注意：延迟不在前 5。** 对于大多数开发者，100ms 和 1ms 的差异在产品层面完全不可感知。速度是加分项，不是主卖点。

### 2.3 评分机制

| 维度 | 说明 |
|------|------|
| 评分计算 | 所有用户打分的加权平均 |
| 用户可修改 | 用户可以随时回来改评分和评价 |
| 提供方不可改 | 不能删差评，不能改分数 |
| 提供方可回复 | 公开回复差评——展示服务态度 |

> **关键启示：高评分 = 期望差小。** 开发者预期"一个能用的 IP API"，实际拿到"城市准 + 有安全标签 + 免费量大"，就是 5 星。如果吹"最快最准"然后城市错了，就是 2 星。

---

## 3. 竞品深度分析

### 3.1 RapidAPI 上的主要竞品

| API 名称 | 评分 | 延迟 | 免费额度 | 起售价 | 核心卖点 | 数据源 |
|----------|------|------|----------|--------|----------|--------|
| **Telize** | ⭐9.9 | ~130ms | 1000/天 | $9/月 | 极简 JSON，CORS 支持 | ip-api.com (免费层) |
| **IP Geo Location** (natkapral) | ⭐9.9 | ~184ms | 100/天 | $0/月 | IPv4/IPv6，安全数据 | 自有 + 第三方 |
| **ip2geo.io** (futureapi) | ⭐9.8 | ~100ms | 100/天 | $5/月 | 每日数据刷新，多币种 | 自有 |
| **User IP Data** (rapihub) | ⭐9.7 | ~221ms | 1000/月 | $7/月 | ISP、ASN、货币、国旗 | 自有 |
| **IP Geolocation** (ipgeolocation.io) | ⭐9.2 | ~993ms | 1000/天 | $15/月 | 安全模块、批量最多 50K | 自有 |
| **IP2Location** | — | — | 500/月 | $15/月 | 代理检测、欺诈评分 | IP2Location |
| **BigDataCloud** | — | — | 1000/月 | ~$10/月 | 专利技术、连接数据 | 自有 |
| **All-in-One** (420vijay47) | — | ~9418ms | 100/天 | $0/月 | VPN/代理/Tor 检测 | 不明 |

### 3.2 竞品定价详细对比

| 提供方 | Free | Starter | Pro | Business |
|--------|------|---------|-----|----------|
| **ipgeolocation.io** | 1000/天 | $15/月 (5万/月) | $50/月 (20万/月) | $100/月 (50万/月) |
| **ip2location.io** | 500/月 | $15/月 (3万/月) | $79/月 (15万/月) | $199/月 (37.5万/月) |
| **Telize** | 1000/天 | $9/月 (1万/月) | $49/月 (15万/月) | $99/月 (30万/月) |
| **User IP Data** | 1000/月 | $7/月 (2.5万/月) | $29/月 (25万/月) | $99/月 (100万/月) |
| **IPGeo（新策略）** | **1万/月** | **$9/月** (10万/月) | **$29/月** (50万+5K风险) | **$79/月** (100万+2.5万风险) |

> IPGeo 在同等价位下配额最高，且独有风险评分引擎。

### 3.3 从开发者视角看竞品：为什么它们拿高分

重新审视竞品的高评分——不是因为延迟、不是因为技术指标，而是因为**完美命中了开发者的真实场景**：

| 竞品 | 评分 | 它真正赢在哪里 | 开发者心理 |
|------|------|-------------|-----------|
| **Telize** | ⭐9.9 | 极简到极致。curl 一行，JSON 干净，5 秒理解全部功能 | "不是在学习 API，是像在用 cat /etc/hosts" |
| **natkapral** | ⭐9.9 | 唯一有 VPN/代理/Tor 检测的。只有它做 | "就它有安全标签，虽然慢但我就要这个" |
| **ip2geo.io** | ⭐9.8 | "每日数据刷新"给了准确度的信心。$5 起步最便宜 | "数据新鲜 + 价格能接受" |
| **User IP Data** | ⭐9.7 | 国旗 emoji 🇺🇸、货币符号——前端直接渲染 | "省了我一个映射步骤" |

**五个规律：**

| 规律 | 说明 |
|------|------|
| **承诺 ≤ 交付** | 不吹牛，默默交付，超出预期 |
| **20% 字段解决 80% 场景** | Telize 只有 7 个字段，够了 |
| **有一个"不可替代的点"** | natkapral 的安全检测——只有它有 |
| **开发者体验是小事的和** | 国旗 emoji、一行 curl、响应键名直觉 |
| **稳定性是隐形的 5 星** | 不宕、不改格式、不来事 |

### 3.4 竞品弱点 → IPGeo 进攻点（更新）

| 竞品弱点 | IPGeo 策略 |
|----------|-----------|
| 所有高评竞品使用免费数据源，城市准确度 40-60% | **全计划 GeoIP2，95%+**，试用第一秒城市必须对 |
| natkapral 的安全标签是唯一壁垒，但仅三个 boolean | **安全标签全计划白送** + Pro 以上有评分和置信度 |
| 免费额度极低（100-1000/天），PoC 不够用 | 免费 **10,000/月**，够完整项目开发 |
| 竞品安全检测只有标签，无评分无解释 | **Risk 引擎**：评分 + 置信度 + verdict + 可解释原因 |
| RapidAPI 上没有任何 IP 风险评分产品 | **蓝海空白**：IPGeo Risk 独占品类 |
| 从地理定位换到风控 API 需要重新注册对接 | **零迁移成本**：同一 Key，同一端点，升级即用 |

---

## 4. IPGeo 核心竞争力

### 4.1 战略框架：红海引流 + 蓝海变现

```
                    蓝海（利润层）
                  ┌──────────────┐
                  │  IPGeo Risk   │
                  │  风险评分引擎   │
                  │  $29-199/月   │
                  │  低竞争高利润   │
                  └──────┬───────┘
                         │ 同一 Key，零迁移成本
                  ┌──────┴───────┐
                  │ IPGeo Location │
                  │  地理定位 API   │
                  │  Free-$79/月   │
                  │  高竞争高流量   │
                  └──────────────┘
                    红海（引流层）
```

- **红海（Location）**：开发者搜 "IP geolocation" 找到你 → 免费 10K/月 → 城市 95%+ 准确 → 安全标签白送 → 留下 → 评分高
- **蓝海（Risk）**：同一个开发者做风控时 → 在响应里看到 `meta.upgrade` → 同一个 Key 升级 → 代码零改动 → 付费

### 4.2 核心竞争力一：数据准确度（根基）

**所有计划统一使用 MaxMind GeoIP2 付费数据库，城市级准确率 95%+。**

这是 IPGeo 与 RapidAPI 竞品最大的差距。Telize（⭐9.9）、natkapral（⭐9.9）、User IP Data（⭐9.7）均使用免费数据源（GeoLite2 或 ip-api.com 免费层），城市准确度普遍在 40-60%。

| 字段 | GeoIP2 准确率 | 竞品免费数据源 | 差距 |
|------|-------------|-------------|------|
| 国家 | 99.8% | 99%+ | 小 |
| ISP / ASN | 98%+ | 90-95% | 可接受 |
| 城市 | **95%+** | 37-60% | **决定性** |
| 邮政编码 | 90%+ | ~30% | 大 |
| 行政区划 | 95%+ | ~50% | 大 |

> **开发者试用的第一秒查自己 IP，城市必须对。** 这是评分的根基。Free 用 GeoIP2 的增量成本为零（固定年费），换来的是试用体验的质变。

### 4.3 核心竞争力二：安全标签全计划免费

**VPN / 代理 / Tor / 数据中心检测，Free 计划就包含。**

引入 IP2Location PX8 数据库（$199/年）做准确检测。RapidAPI 上唯一做安全检测的竞品 natkapral（⭐9.9）以此为核心壁垒——IPGeo 把它白送了。

| 安全字段 | Free | Starter | Pro | Business |
|----------|------|---------|-----|----------|
| is_vpn | ✅ | ✅ | ✅ | ✅ |
| is_proxy | ✅ | ✅ | ✅ | ✅ |
| is_tor | ✅ | ✅ | ✅ | ✅ |
| is_hosting | ✅ | ✅ | ✅ | ✅ |
| network_type | ✅ | ✅ | ✅ | ✅ |
| **risk_score (0-100)** | — | — | ✅ | ✅ |
| **flags + confidence** | — | — | ✅ | ✅ |
| **abuse_reports** | — | — | ✅ | ✅ |
| **verdict + recommendation** | — | — | ✅ | ✅ |

### 4.4 核心竞争力三：Risk 评分引擎（蓝海独占）

RapidAPI 上**没有一个** IP API 提供可解释的风险评分。竞品最多返回 boolean 标签（"是代理吗？true"）。

IPGeo Risk 的评分引擎：

```
输入 IP
    │
    ├─→ IP2Location PX8 代理检测
    │     Tor(+50) / VPN(+40) / 公共代理(+40) / 住宅代理(+35)
    │
    ├─→ GeoIP2 网络类型检测
    │     数据中心(+15) / ASN 类型
    │
    ├─→ AbuseIPDB 滥用情报
    │     报告数(+25 加权) / 报告类型 / 时间范围
    │
    └─→ 规则引擎聚合 → 阈值映射
          0-30  → low      → allow
          31-60 → medium   → flag
          61-80 → high     → challenge
          81-100 → critical → block
```

**每个判断都有解释。** 安全团队看得懂 → 推给开发接 → 开发信任 → 不因一次误判换竞品。

### 4.5 核心竞争力四：零迁移成本的升级路径

Location 和 Risk 是**同一个 API Key、同一个 Base URL、同一套 JSON 结构**。

```
Free 用户 (Location only)
        ↓
项目需要风控
        ↓
在响应 meta.upgrade 里看到 Risk 产品
        ↓
升级到 Pro — 同一个 Key
        ↓
同一个端点，响应里多了 risk 对象
        代码零改动 ✅
```

换竞品做风控 = 重新注册、重新对接、重新改适配代码。IPGeo = 换个 Plan。

### 4.6 成本结构优势（底层支撑）

| 成本项 | 竞品（upstream API 模式） | IPGeo（本地数据库模式） |
|--------|--------------------------|------------------------|
| 每次查询边际成本 | 有（付给数据提供商） | **零** |
| 数据库许可 | 隐含在 API 价格中 | GeoIP2 $300/年 + IP2Location $199/年（固定） |
| 扩展成本 | 随请求量线性增长 | **几乎不变**（内存/CPU） |

**年固定成本 $499，2 个 Pro 用户回本。** 之后每个新用户都是增量利润。

---

## 5. 定价策略

### 5.1 定价原则

1. **Free 体验即真品** — 用 GeoIP2 真实数据 + 安全标签，试用体验决定留存
2. **免费额度够 PoC** — 10,000/月，足够小项目完整开发周期，竞品 100-1000/天远远不够
3. **Starter → Pro 的价值跳跃是 Risk** — 不是数据精度（全部已有），是风险评分 + 更高频率
4. **风险评分单独定价** — Risk 查询有单独配额，不与 Location 混淆
5. **价格低于竞品 30-50%** — 成本结构允许

### 5.2 IPGeo Location 定价表（红海）

| 计划 | 月价 | 月配额 | 速率/分钟 | 核心差异 |
|------|------|--------|-----------|----------|
| **FREE** | $0 | 10,000 | 60 | GeoIP2 全数据 + 安全标签免费 |
| **STARTER** | **$9** | 100,000 | 600 | 更高速率 |
| **PRO** | **$29** | 500,000 | 3,000 | **+ Risk 评分 5K 次/月** + 专用支持 |
| **BUSINESS** | **$79** | 1,000,000 | 10,000 | **+ Risk 评分 25K 次/月** + SLA |
| **ENTERPRISE** | 定制 | 无限 | 无限 | 全部 + 私有部署可选 |

### 5.3 IPGeo Risk 独立定价（蓝海，第二个 RapidAPI 列表）

| 计划 | 月价 | 风险查询/月 | 适用 |
|------|------|-----------|------|
| **RISK LITE** | $0 | 100 | 试用 |
| **RISK PRO** | **$29** | 5,000 | 小团队风控 |
| **RISK BUSINESS** | **$79** | 25,000 | 中型 SaaS/电商 |
| **RISK ENTERPRISE** | 定制 | 无限 | 私有部署 |

> **注意：** Location 的 Pro 计划已包含 5K 风险查询，Business 包含 25K。用户不需要单独买 Risk——除非他只需要 Risk 不需要 Location。

### 5.4 与竞品价格对比

| 计划档位 | IPGeo | ipgeolocation.io | ip2location.io | Telize | User IP Data |
|----------|-------|------------------|----------------|--------|-------------|
| Starter (~10万/月) | **$9** | $15 | $15 | $9 | $7 |
| Pro (~50万/月) | **$29** + 风险评分 | $50 | $79 | $49 | $29 |
| Business (100万/月+) | **$79** + 风险评分 | $100+ | $199 | $99 | $99 |

> IPGeo 在所有档位上价格最低或持平，配额最高，且**独有风险评分**。

### 5.5 免费计划策略

**为什么给 10,000/月 + GeoIP2 + 安全标签？**

1. **试用即真品** — 开发者体验到的就是付费产品的数据质量，不会因为 GeoLite2 不准而流失
2. **10,000/月**够支撑完整 PoC，竞品给 100-1000/天只够试几次
3. **安全标签白送**拆了 natkapral 的唯一壁垒——你有的我免费就有
4. **边际成本为零** — 多 10,000 次查询不增加一毛钱成本
5. **口碑传播** — 免费用户体验好 → 在社区自发推荐 → 更多人来

### 5.6 盈亏平衡

```
月固定成本：~$52
  - VPS: ~$10/月
  - GeoIP2 City + ISP: $25/月摊销 ($300/年)
  - IP2Location PX8: $16.6/月摊销 ($199/年)

保本线（RapidAPI 佣金后 20%）：
  2 个 Pro 用户 ($23.2×2 = $46.4) → 接近打平
  3 个 Pro 用户 ($23.2×3 = $69.6) → 盈利 ✅
  或：6 个 Starter + 1 个 Pro → 盈利
```

---

## 6. API 产品设计

### 6.1 端点设计

| 端点 | 用途 | 鉴权 | 计划 |
|------|------|------|------|
| `GET /v1/ip/{ip}` | 查询指定 IP（含地理+安全标签） | X-RapidAPI-Key | 全部 |
| `GET /v1/ip/{ip}?include=risk` | 查询 IP + 风险评分 | X-RapidAPI-Key | Pro+ |
| `GET /v1/ip/me` | 查询调用方 IP | X-RapidAPI-Key | 全部 |
| `POST /v1/ip/batch` | 批量查询（最多 100） | X-RapidAPI-Key | 全部 |
| `GET /v1/usage` | 查询当月用量 | X-RapidAPI-Key | 全部 |
| `GET /v1/health` | 健康检查 | 无 | 全部 |

### 6.2 RapidAPI 特有 Header 处理

| Header | 用途 |
|--------|------|
| `X-RapidAPI-Key` | 最终用户的 API Key |
| `X-RapidAPI-User` | RapidAPI 用户 ID（用于配额追踪） |
| `X-RapidAPI-Subscription` | 订阅计划（FREE/BASIC/PRO/ULTRA/MEGA） |
| `X-RapidAPI-Proxy-Secret` | **平台签名密钥**（必须 HMAC 验证） |
| `X-RapidAPI-Request-Id` | 请求 ID（用于去重/排查） |

### 6.3 响应格式（v2）

按开发者使用场景分组为 `location` / `network` / `security` / `meta`，不用平铺 30 个字段：

**Free/Starter 响应：**

```json
{
  "ip": "8.8.8.8",
  "location": {
    "country":      {"code": "US", "name": "United States"},
    "continent":    {"code": "NA", "name": "North America"},
    "city":         "Mountain View",
    "region":       "California",
    "postal_code":  "94043",
    "latitude":     37.4223,
    "longitude":    -122.0842,
    "accuracy_km":  10,
    "timezone":     "America/Los_Angeles"
  },
  "network": {
    "isp":   "Google LLC",
    "asn":   15169,
    "type":  "hosting"
  },
  "security": {
    "is_tor":      false,
    "is_vpn":      false,
    "is_proxy":    false,
    "is_hosting":  true
  },
  "meta": {
    "data_source": "GeoIP2",
    "upgrade": {
      "risk_scoring": "Get risk_score, confidence, and abuse reports on Pro+",
      "learn_more":   "https://getipgeo.com/risk"
    }
  }
}
```

**Pro+ 响应（额外包含 risk 对象）：**

```json
{
  "ip": "45.33.32.156",
  "location": { "..." },
  "network":   { "..." },
  "security": {
    "is_tor":      false,
    "is_vpn":      true,
    "is_proxy":    false,
    "is_hosting":  true
  },
  "risk": {
    "score":       85,
    "level":       "high",
    "verdict":     "recommend_block",
    "confidence":  0.92,
    "flags": [
      {
        "type":       "vpn",
        "confidence": 0.99,
        "source":     "ip2location_px8",
        "last_seen":  "2026-06-15"
      },
      {
        "type":       "data_center",
        "confidence": 0.95,
        "source":     "asn_type",
        "detail":     "AS63949 Linode LLC — known hosting provider"
      },
      {
        "type":           "abuse_reports",
        "confidence":     0.78,
        "source":         "abuseipdb",
        "report_count":   3,
        "reporter_count": 2,
        "categories":     ["SSH brute-force", "spam"],
        "detail":         "3 reports in last 90 days from 2 independent reporters"
      }
    ],
    "recommendation": {
      "action":    "challenge_or_block",
      "reasoning": "VPN detected with high confidence + recent abuse reports from 2 independent sources"
    }
  }
}
```

**设计原则：**
- **分组不铺平** — 开发者一秒找到他要的区块
- **每个判断有解释** — flags 里标注 source 和 confidence
- **meta.upgrade 是钩子** — 不打扰但可见，Free 用户自然发现 Risk

### 6.4 字段选择逻辑

**为什么有这些字段（而不是更多）：**

| 你在竞品里看到的 | IPGeo 要不要 | 理由 |
|------|-----------|------|
| 国家/城市/坐标 | ✅ 有 | 基础需求 |
| ISP / ASN | ✅ 有 | 网络诊断刚需 |
| 时区 | ✅ 有 | 内容本地化 |
| 安全标签 | ✅ 免费 | 拆竞品壁垒 |
| 风险评分 | ✅ Pro+ | 蓝海独占 |
| 国旗 emoji 🇺🇸 | 考虑加 | User IP Data 靠这个拿印象分 |
| 货币代码 EUR | 考虑加 | 电商场景需要 |
| 语言代码 en | 考虑加 | 内容本地化需要 |
| 收入水平 | ❌ 不加 | GeoIP2 Insights 才有，暂不引入 |
| 人口统计 | ❌ 不加 | 太细分，初期不需要 |

### 6.5 OpenAPI Spec 优化清单

- [ ] 每个端点写场景描述（不仅是字段列表）
- [ ] 设置可运行的示例 IP 值（8.8.8.8 / 1.1.1.1）
- [ ] 提供 curl / Python / Node.js / PHP / Go 代码示例
- [ ] 上传 Logo（500×500px）和 Banner
- [ ] 添加 "Works great for" 区块：广告定向 / 反欺诈 / 内容本地化 / 数据分析
- [ ] 标注安全标签是全部计划免费包含的
- [ ] 标注数据源为 GeoIP2（95%+ city accuracy）

---

## 7. 技术实施方案

### 7.1 Phase 0：数据升级（已计划，待执行）

**目标：全计划 GeoIP2 + IP2Location PX8 集成**

| 序号 | 任务 | 说明 |
|------|------|------|
| 0.1 | 购买 MaxMind GeoIP2 City + ISP | maxmind.com，$300/年 |
| 0.2 | 下载 .mmdb 文件，上传 VPS data/ | 替换 GeoLite2 文件 |
| 0.3 | 购买 IP2Location PX8 | ip2location.com，$199/年 |
| 0.4 | 下载 PX8.BIN + Python reader | 放到 data/ 和 app/ |
| 0.5 | 删除 GeoLite2 文件 | 清理残留 |

### 7.2 Phase 1：代码改造（待执行）

**改动清单：**

| 文件 | 改动 | 行数 |
|------|------|------|
| `app/geodb.py` | 新增 `_detect_network_type()` + `_security_tags()` | +50 |
| `app/proxy_db.py` | **新增** — IP2Location PX8 包装器 | ~80 |
| `app/abuse.py` | **新增** — AbuseIPDB 缓存层 (Redis 24h TTL) | ~80 |
| `app/risk.py` | **新增** — 风险评分规则引擎 | ~150 |
| `app/main.py` | 响应格式重构 (location/network/security/meta 分组) | +40 |
| `app/config.py` | 新增 `abuseipdb_api_key`, `ip2location_proxy_db_path` | +3 |
| `app/billing.py` | 新增 `RISK_QUOTAS` + `deduct_risk()` | +20 |
| `tests/test_api.py` | 新增 `TestSecurity` + `TestRisk` (约 8 个测试) | +100 |
| **总计** | | **~523 行** |

### 7.3 架构概览（更新后）

```
RapidAPI 用户
    │
    ▼
RapidAPI Gateway
    │  注入 X-RapidAPI-* headers
    ▼
IPGeo API (api.getipgeo.com)
    │
    ├─ RapidAPI 中间件 (已有 ✅)
    │   ├─ 验证 X-RapidAPI-Proxy-Secret (HMAC)
    │   ├─ 从 X-RapidAPI-Subscription 映射计划
    │   └─ 按 X-RapidAPI-User 追踪配额
    │
    ├─ GeoIP 查询引擎
    │   ├─ GeoIP2 City + ISP (本地 mmap) — 全计划
    │   └─ IP2Location PX8 (本地 BIN) — 安全标签
    │
    ├─ Risk 评分引擎 (新增 🔵)
    │   ├─ IP2Location PX8 → VPN/代理/Tor 检测
    │   ├─ AbuseIPDB → 滥用情报 (Redis 缓存 24h)
    │   ├─ ASN 类型 → 数据中心/住宅/移动
    │   └─ 规则引擎 → 评分 0-100 + verdict
    │
    └─ Redis
        ├─ 速率限制（滑动窗口）
        ├─ 月度配额追踪
        ├─ 风险查询配额
        └─ AbuseIPDB 缓存
```

### 7.4 部署步骤

1. Phase 0：购买 + 下载数据库，上传 VPS
2. Phase 1：代码改造 + 测试（48 tests → ~56 tests）
3. 更新 VPS `.env`：`IPGEO_RAPIDAPI_PROXY_SECRET` + `ABUSEIPDB_API_KEY` + `IP2LOCATION_PROXY_DB_PATH`
4. `docker compose up -d --build` 部署
5. RapidAPI 测试控制台验证鉴权、计费、响应格式
6. 提交审核 → 公开到市场

---

## 8. 营销推广计划

### 8.1 IPGeo 的新定位语

**旧定位（废弃）：**
> ~~"Fastest IP Geolocation API (<1ms, 95%+ City Accuracy)"~~

**新定位：**
> **"Accurate IP Geolocation API — 95%+ City Accuracy, Built-in Security Detection, Free 10K/mo"**

**Risk 定位：**
> **"IP Risk Scoring API — VPN/Proxy/Tor Detection with Confidence Scores & Abuse Intelligence"**

### 8.2 RapidAPI 列表 SEO（关键词 + 标签）

**Location 列表标签：**
```
ip-geolocation, ip-lookup, geoip, ip-api, geolocation, ip-to-location,
asn-lookup, ip-data, vpn-detection, proxy-detection, tor-detection,
ip-city-lookup, batch-ip-lookup
```

**Risk 列表标签：**
```
ip-risk, fraud-detection, vpn-detection, proxy-detection, tor-detection,
ip-reputation, abuse-detection, risk-scoring, threat-intelligence,
ip-fraud-score
```

### 8.3 前 30 天运营策略

| 时间 | 行动 | 目标 |
|------|------|------|
| **上线日** | Lists 公开。通知 TG | 首个 5 星评分 |
| **Day 1-3** | 在 Questions 区预写 FAQ，主动回复 | 零等待体验 |
| **Day 3-7** | 主动联系前 20 个注册用户，礼貌邮件问体验 | 前 10 个评价 |
| **Day 7-14** | 根据反馈调整文档/文案 | 优化转化 |
| **Day 14-30** | 在 dev.to 发布第一篇技术文章 | 站外引流 |

**不做的：**
- ❌ Launch 折扣 / 限时免费 — 给开发者的信号是"这个产品不值原价"
- ❌ 虚假评价 — RapidAPI 有检测，封号得不偿失
- ❌ HN / Reddit 首日发布 — 等有 5 个 5 星评价后再发

### 8.4 内容营销主题（更新）

旧主题围绕"速度"（How We Built the Fastest... / Why Your API Is Slow...）→ 废弃。

新主题围绕**准确度 + 安全 + 开发者体验**：

1. **"We Switched from GeoLite2 to GeoIP2 — Here's What Changed for Our Free Users"** (dev.to)
2. **"Every IP API Has VPN Detection. None of Them Tell You Why."** — Risk 引擎设计理念
3. **"Building a Fraud Detection System with 3 API Calls"** — IPGeo Location + Risk 实战
4. **"What Makes a 5-Star API on RapidAPI? We Analyzed 8 IP Geolocation APIs"** — 竞品分析透明分享
5. **"From Free to Pro: How We Designed Zero-Migration Upgrades for API Pricing"** — 产品设计思考

### 8.5 增长飞轮

```
开发者搜索 "IP geolocation API"
    ↓
在 RapidAPI 发现 IPGeo（高评分 + 免费 10K + 安全标签）
    ↓
试用，curl 跑通，城市对了，安全标签有
    ↓
接入项目。Location 跑着跑着，风控需求出现
    ↓
响应里 meta.upgrade 已提示 Risk 产品
    ↓
升级到 Pro ($29/月) — 同一 Key，零代码改动
    ↓
满意 → 写好评 / 在团队内推 / 分享到社区
    ↓
更多开发者在 RapidAPI 搜索时看到高评分
    ↓
循环 🔄
```

### 8.6 关键指标

| 指标 | 3 个月目标 | 6 个月目标 | 追踪方式 |
|------|-----------|-----------|----------|
| RapidAPI 评分 | **≥ 4.5** | **≥ 4.8** | 平台 |
| 免费注册 | 50+/月 | 200+/月 | Redis 计数 |
| 免费→付费转化 | >8% | >10% | RapidAPI Analytics |
| Risk 采纳率 (付费用户中) | >30% | >50% | 后端 |
| Questions 响应时间 | <2h | <1h | 手动 |
| 首月留存 | >60% | >70% | 按月活跃 Key |

---

## 9. 时间线与里程碑

### Phase 0：数据升级（第 1 周前半）

| 任务 | 时间 | 费用 |
|------|------|------|
| 购买 MaxMind GeoIP2 City + ISP | 30 分钟 | $300 |
| 下载 + 上传 VPS | 20 分钟 | $0 |
| 购买 IP2Location PX8 | 30 分钟 | $199 |
| 下载 PX8 BIN + Python reader | 20 分钟 | $0 |
| 删除旧 GeoLite2 文件 | 5 分钟 | $0 |
| **合计** | **~2 小时** | **$499** |

### Phase 1：代码改造（第 1 周后半）

| 任务 | 时间 |
|------|------|
| `app/proxy_db.py` — IP2Location 包装器 | 1 小时 |
| `app/abuse.py` — AbuseIPDB 缓存层 | 1 小时 |
| `app/risk.py` — 风险评分引擎 | 2 小时 |
| `app/geodb.py` — network_type + security_tags | 1 小时 |
| `app/main.py` — 响应格式重构 | 1 小时 |
| `app/billing.py` — Risk 配额 | 30 分钟 |
| `tests/test_api.py` — 新增测试 | 1 小时 |
| 跑测试 + 修复 | 30 分钟 |
| 部署 VPS | 30 分钟 |
| **合计** | **~1.5 天** |

### Phase 2：RapidAPI 上线（第 2 周）

| 日期 | 行动 |
|------|------|
| **Day 1** | 完成 RapidAPI Dashboard 端点配置 |
| **Day 1** | 填列表文案（新定位语） |
| **Day 1** | 配置 Plans & Pricing |
| **Day 1** | 获取 Proxy Secret → 配置 VPS .env |
| **Day 2** | RapidAPI 测试控制台端到端验证 |
| **Day 2** | 提交审核 |
| **Day 3-6** | 等待审核（2-5 天） |
| **审核通过日** | 发布到公开市场 |

### Phase 3：Risk 独立上线 + 直售站更新（第 3-4 周）

| 任务 | 时间 |
|------|------|
| 创建 IPGeo Risk 独立 RapidAPI 列表 | 1 天 |
| Risk 列表文案 + 定价 + 端点 | 1 天 |
| 更新 getipgeo.com 首页（定位语 + 功能表） | 1 天 |
| 新增 /products/risk 页面 | 1 天 |
| dev.to 首发技术文章 | 1 天 |

### Phase 4：增长期（第 2-3 月）

| 周次 | 重点 |
|------|------|
| 第 5-6 周 | 收集用户反馈，迭代 Risk 评分规则 |
| 第 7-8 周 | 根据数据优化定价/文案 |
| 第 9-10 周 | 交叉推广 + 第二篇博文 |
| 第 11-12 周 | 自建滥用数据库（网络效应） |

### Phase 5：稳定期（第 4-8 月）

- RapidAPI 月收入目标：**$500 → $2,000+**
- Paddle 直售同步启动（审核通过后）
- 两个渠道对比数据，指导资源分配
- 企业私有部署容器（$499-999/月）

---

## 10. 费用预算

### 10.1 一次性投入（Phase 0）

| 项目 | 金额 | 用途 |
|------|------|------|
| MaxMind GeoIP2 City | $200/年 | 城市/坐标/时区/邮编 .mmdb |
| MaxMind GeoIP2 ISP | $100/年 | ISP/ASN .mmdb |
| IP2Location PX8 | $199/年 | VPN/代理/Tor/住宅代理检测 .BIN |
| **合计** | **$499/年** | |

### 10.2 月度运营

| 项目 | 月均 | 备注 |
|------|------|------|
| VPS | ~$10 | 已有 |
| 域名 | ~$0.8 | getipgeo.com，已有 |
| GeoIP2 摊销 | $25 | $300/12 |
| IP2Location 摊销 | $16.6 | $199/12 |
| AbuseIPDB | $0 | 免费层 1000 次/天 |
| RapidAPI 佣金 | 收入的 20% | 只有付费用户涉及 |
| **固定月均** | **~$52** | 不含佣金 |

### 10.3 回报预估

| 付费用户数 | 月收入 (佣金后) | 年回收 | ROI |
|-----------|----------------|--------|-----|
| 2 个 Pro | $46.4 | $557 | **回本** |
| 5 个 Pro + 2 个 Business | $242 | $2,904 | 5.8× |
| 10 个 Pro + 5 个 Business | $548 | $6,576 | 13.2× |
| 20 个 Pro + 10 个 Business + 1 Enterprise | $1,348 | $16,176 | 32.4× |

---

## 11. 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| **首波用户评分翻车** | 中 | 高 | GeoIP2 全计划确保试用数据准确；上线首周主动跟进前 20 个用户；差评 2h 内公开回复并修复 |
| RapidAPI 审核不通过 | 低 | 高 | 提前阅读审核标准，确保 OpenAPI 规范正确、描述完整 |
| **IP2Location PX8 数据质量不达预期** | 低 | 中 | 先用 AbuseIPDB 交叉验证；标注 confidence 而非 boolean；数据源透明 |
| AbuseIPDB 免费层不够用 | 中 | 低 | Redis 24h 缓存降低 API 调用量；$14/月升级即可 |
| 竞品跟进（natkapral 也免费安全标签） | 中 | 中 | 它做不了评分和置信度——Risk 才是壁垒；且免费标签它可能扛不住成本 |
| 用户量大导致 VPS 过载 | 低 | 高 | 当前 4 workers 可撑 10 万 QPS；加 Cloudflare CDN + 横向扩展 |
| 负面评价 | 低 | 中 | 不删差评，公开回复并修掉问题。差评+真诚回复 > 无评价 |
| Paddle 突然通过审核 | 低 | 低 | 两个渠道并行，代码里 RapidAPI 标志位区分计费来源 |
| RapidAPI 更改分成比例 | 低 | 中 | 不依赖单一渠道，继续建设 getipgeo.com 直售 |
| MaxMind / IP2Location 授权模式变更 | 低 | 中 | 数据库本地已下载，不受影响；年费不续仍有最终版本可用 |
| **Risk 评分误判导致用户严重损失** | 极低 | 极高 | 免责声明 + 评分非"事实"是"风险评估" + verdict 是建议不是决策 |

---

## 12. 附录

### A. RapidAPI 搜索关键词矩阵

按场景分组：

| 场景 | 搜索词 | 目标产品 |
|------|--------|----------|
| 地理定位 | `ip geolocation`, `ip lookup`, `geoip`, `ip to location`, `ip api` | Location |
| 城市级 | `ip city lookup`, `ip to city`, `city geolocation` | Location |
| 网络信息 | `asn lookup`, `isp lookup`, `ip to isp` | Location |
| 批量处理 | `batch ip lookup`, `bulk ip lookup`, `ip enrichment` | Location |
| 安全/风控 | `vpn detection`, `proxy detection`, `tor detection`, `ip fraud detection` | Risk |
| 威胁情报 | `ip risk score`, `ip reputation`, `threat intelligence ip`, `ip abuse check` | Risk |

### B. 竞品字段对比速查（更新）

| 提供方 | 国家 | 城市 | ISP | ASN | 时区 | 邮编 | 安全标签 | 风险评分 | 城市准确率 |
|--------|------|------|-----|-----|------|------|---------|---------|-----------|
| **IPGeo** (新) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 免费 | ✅ Pro+ | **95%+** |
| Telize | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ~50% |
| natkapral | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 仅标签 | ❌ | ~50% |
| ip2geo.io | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ~60% |
| User IP Data | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ~50% |
| ipgeolocation.io | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 付费 | ❌ | ~60% |

### C. 参考链接

- [RapidAPI Provider Dashboard](https://rapidapi.com/provider/)
- [RapidAPI Listing Best Practices](https://docs.rapidapi.com/docs/listing-best-practices)
- [RapidAPI Pricing Recommendations](https://docs.rapidapi.com/docs/pricing-your-api)
- [MaxMind GeoIP2 购买](https://www.maxmind.com/en/geoip2-databases)
- [IP2Location Proxy Database](https://www.ip2location.com/database/px8-ip-proxytype-country)
- [AbuseIPDB API](https://docs.abuseipdb.com/)
- [IPGeo 官网](https://getipgeo.com/)

---

> **下一步行动**：确认计划 v2.0 后，执行 Phase 0（购买数据库 $499），然后 Phase 1（代码改造 ~1.5 天），Phase 2（RapidAPI 上线）。
>
> **一句话：$499 启动，2 个用户回本，红海做量，蓝海做利。**
