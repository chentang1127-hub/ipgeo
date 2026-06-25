# IPGeo 30 天推流计划：300 免费用户 + 10 付费用户

> 目标：2026-06-26 → 2026-07-25
> 执行人：唐高生 + Claude（运营执行）

---

## 目标拆解

```
300 免费用户
  = 6,000 网站访问（5% 注册率）
  = 200 访问/天

访问来源拆解：
  Stack Overflow:  80/天  (40%)  ← 主引擎
  Reddit:          40/天  (20%)  ← 第二引擎
  PyPI/npm:        30/天  (15%)
  SEO/直接:        30/天  (15%)  
  Dev.to/Hashnode: 20/天  (10%)

10 付费用户 = 3.3% 免费→付费转化
```

---

## 执行节奏

```
Week 1 (6/26-7/2):  基建 —— Stack Overflow 账号声望 + GitHub 初始化 + 内容储备
Week 2 (7/3-7/9):   冷启动 —— 首批回答 + Reddit 发帖 + Dev.to 同步
Week 3 (7/10-7/16): 扩量 —— 批量回答 + 第二波内容 + 数据分析
Week 4 (7/17-7/25): 优化 —— 砍掉无效渠道 + 加倍有效渠道 + 冲线
```

---

## Week 1：基建（6/26 - 7/2）

### 第 1 天（6/26 周四）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **GitHub ipgeo 仓库初始化** — 补 .git、推 social preview、加 topics 标签 (`ip-geolocation`, `geoip`, `security`, `api`)、README 加 Demo curl 和徽章 | 30 min | 仓库可 Star |
| 2 | **GitHub ipgeo-python 仓库初始化** — 同上，补 git | 15 min | Python SDK 仓库 |
| 3 | **GitHub ipgeo-js 仓库初始化** — 同上 | 15 min | JS SDK 仓库 |
| 4 | **GitHub Awesome list PR** — 搜索 `awesome-ip` `awesome-geoip` 列表，提交 1 个 PR 把 IPGeo 加进去 | 30 min | 第一个外链 |
| 5 | **Stack Overflow 账号注册** — 完善 profile，头像，bio（含 getipgeo.com 链接） | 15 min | 账号就绪 |

**今日目标：** 3 个 GitHub 仓库有 README + topics + social preview

### 第 2 天（6/27 周五）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **Stack Overflow 搜索** — 搜 "ip geolocation" "ipinfo" "geoip" "ip location api"，找出 15 个有流量的问题 | 30 min | 问题清单 |
| 2 | **回答前 3 个** — 高质量回答（不硬推 IPGeo，自然引用 `curl` 示例） | 60 min | 3 个回答 |
| 3 | **Reddit 账号准备** — 加入 r/webdev, r/Python, r/node, r/SaaS, r/SideProject | 15 min | 账号就绪 |
| 4 | **博文 #2 撰写** — "IPinfo Alternative: Same Data, 60% Cheaper" | 45 min | 博文完成 |

**今日目标：** 3 个 SO 回答 + 1 篇博文

### 第 3 天（6/28 周六）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **博文 #2 发布** — 挂到 getipgeo.com/blog，同步 Dev.to + Hashnode | 30 min | 3 个平台的内容 |
| 2 | **博文 #3 撰写** — "How to Get IP Location in Python (3 Lines)" | 45 min | 博文完成 |
| 3 | **Stack Overflow 回答 2 个** | 30 min | 累计 5 个回答 |
| 4 | **API 目录提交** — apilist.fun, freepublicapis.com, publicapis.io（3 个） | 30 min | 外链 + 流量 |

**今日目标：** 博文 #2 上线、累计 5 个 SO 回答

### 第 4 天（6/29 周日）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **博文 #3 发布** — 网站 + Dev.to + Hashnode | 30 min | 内容 |
| 2 | **Reddit r/Python 发布** — "I built a free IP geolocation library for Python (pip install ipgeo-api)" | 20 min | 社区帖 |
| 3 | **博文 #4 撰写** — "How to Detect VPN/Proxy Users from IP Address" | 45 min | 安全方向内容 |
| 4 | **Stack Overflow 回答 2 个** | 30 min | 累计 7 个回答 |

**今日目标：** 博文 #3 上线、Reddit 第一篇

### 第 5 天（6/30 周一）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **博文 #4 发布** — 网站 + Dev.to + Hashnode | 30 min | 内容 |
| 2 | **Reddit r/node 发布** — "IPGeo JS SDK — npm install ipgeo-api" | 20 min | 社区帖 |
| 3 | **博文 #5 撰写** — "Free IP Geolocation API — 10K/Month, No Credit Card" | 45 min | 内容 |
| 4 | **Stack Overflow 回答 2 个** | 30 min | 累计 9 个回答 |

**今日目标：** 博文 #4 上线、JS 社区帖

### 第 6 天（7/1 周二）

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **博文 #5 发布** — 网站 + Dev.to + Hashnode | 30 min | 内容 |
| 2 | **Reddit r/SideProject 发布** — "Show /r/SideProject: IPGeo — free IP geolocation API with built-in security detection" | 20 min | 社区帖 |
| 3 | **Stack Overflow 回答 2 个** | 30 min | 累计 11 个回答 |
| 4 | **API 目录提交** — 再提交 3 个（mixedanalytics.com/api-list 等） | 30 min | 外链 |

**今日目标：** 5 篇博文全上线、累计 11 个 SO 回答

### 第 7 天（7/2 周三）— Week 1 复盘

| # | 动作 | 预计耗时 | 产出 |
|---|------|---------|------|
| 1 | **数据复盘** — 查看 Google Analytics、PyPI 下载、npm 下载、注册用户数 | 30 min | 数据 |
| 2 | **Stack Overflow 回顾** — 哪些回答有 upvote？哪些有问题跟进？ | 20 min | 优化策略 |
| 3 | **调整 Week 2 计划** — 根据数据调整 | 30 min | 更新计划 |

**Week 1 累计产出：**
- 3 个 GitHub 仓库就绪（含 social preview、topics）
- 1 个 Awesome list PR
- 11 个 Stack Overflow 回答
- 5 篇博文（网站 + Dev.to + Hashnode 三平台）
- 3 篇 Reddit 帖
- 6 个 API 目录提交

**Week 1 指标目标：**
- GitHub Stars: 15+
- Stack Overflow 回答 upvotes: 累计 20+
- 网站日访问: 50+
- 注册用户: 30+

---

## Week 2：冷启动（7/3 - 7/9）

Week 2 的核心策略：继续 Stack Overflow 高频回答 + Reddit 持续露出 + 分析数据放大有效渠道。

### 每日例行（7/3-7/9，每天 60 min）

| 动作 | 频率 | 耗时 |
|------|------|------|
| Stack Overflow — 回答 2 个新问题 | 每天 | 30 min |
| Stack Overflow — 检查已回答问题的 upvote/评论，跟进 | 每天 | 10 min |
| Reddit — 在 r/webdev r/Python r/node 参与讨论（不硬广） | 每天 | 20 min |

### Week 2 重点行动

| 天 | 额外动作 | 耗时 |
|----|---------|------|
| 7/3 周四 | r/SaaS 发帖 — "How I built an IP geolocation API and got my first paid customer" | 30 min |
| 7/4 周五 | Dev.to 文章推广 — 在相关文章的评论里自然引用 IPGeo | 20 min |
| 7/5 周六 | 写一篇对比/教程相关的帖子发 CSDN（中文市场） | 45 min |
| 7/6 周日 | r/webdev 回答 "what's your favorite free API" 类帖子 | 20 min |
| 7/7 周一 | r/selfhosted 发帖 — 对有 IP 定位需求的帖子推荐 IPGeo | 20 min |
| 7/8 周二 | 查看 PyPI/npm 下载量，如果零则优化 README | 30 min |
| 7/9 周三 | **Week 2 复盘** | 30 min |

**Week 2 累计产出：**
- 14 个新 Stack Overflow 回答（累计 25 个）
- 5 篇 Reddit 帖 + 持续评论参与
- 1 篇 CSDN 文章（中国开发者触达）

**Week 2 指标目标：**
- GitHub Stars: 30+
- Stack Overflow 累计 upvotes: 50+
- 网站日访问: 100+
- 注册用户累计: 80+
- 首次付费用户: 2+

---

## Week 3：扩量（7/10 - 7/16）

Week 3 的核心：停止无效动作，加倍有效渠道。

### 每日例行（7/10-7/16）

| 动作 | 频率 | 耗时 |
|------|------|------|
| Stack Overflow 回答（如果效果好就加倍） | 每天 2-4 个 | 40 min |
| Reddit 监控 + 参与（如果效果好） | 每天 | 20 min |

### Week 3 重点行动

| 天 | 动作 | 耗时 |
|----|------|------|
| 7/10 周四 | 掘金（juejin.cn）发文章 — 中文开发者社区 | 45 min |
| 7/11 周五 | V2EX 发帖 — "做了个免费的 IP 定位 API，求体验" | 20 min |
| 7/12 周六 | 录制 1 个 3 分钟 Loom 视频 — 演示从注册到调用 | 30 min |
| 7/13 周日 | 知乎发文章 — "2026 年最好的免费 IP 定位 API" | 45 min |
| 7/14 周一 | 检查 GitHub issues / PR — 积极回复 | 20 min |
| 7/15 周二 | 分析付费转化漏斗 — 免费用户 registration → usage → upgrade | 30 min |
| 7/16 周三 | **Week 3 复盘** | 30 min |

**Week 3 累计产出：**
- 14-28 个新 SO 回答（累计 40-55 个）
- 3 篇国内社区内容
- 1 个视频 Demo

**Week 3 指标目标：**
- GitHub Stars: 50+
- 网站日访问: 150+
- 注册用户累计: 180+
- 付费用户累计: 5+

---

## Week 4：冲刺（7/17 - 7/25）

### 最后 9 天行动

| 天 | 动作 | 目标 |
|----|------|------|
| 7/17 | SO 回答 4 个（冲刺日） | 最大化 |
| 7/18 | r/startups 发帖 — 分享 IPGeo 创业进展 | 新一轮 Reddit 流量 |
| 7/19 | SEO 内容索引检查 — Google Search Console 看看哪些关键词开始有流量 | 为后续 SEO 铺路 |
| 7/20 | 写一篇"IPGeo 30 天复盘"博文发 Dev.to + Reddit | 真实故事吸引人 |
| 7/21 | SO 回答 4 个 | 最大化 |
| 7/22 | 分析注册用户 — 给他们发邮件？问 feedback？ | 激活沉睡用户 |
| 7/23 | 公众号/知乎第二篇 | 中文流量 |
| 7/24 | 最终数据盘点 | 对账 |
| 7/25 | **Month 1 总结 + Month 2 计划** | 下一阶段 |

**Week 4 指标目标：**
- 注册用户累计: 300+
- 付费用户累计: 10+

---

## 内容日历总览

| 博客 # | 标题 | 目标关键词 | Week |
|--------|------|-----------|------|
| 1 | Best IP Geolocation API 2026 | "best ip geolocation api" | ✅ 已完成 |
| 2 | IPinfo Alternative: Same Data, 60% Less | "ipinfo alternative" | W1 |
| 3 | How to Get IP Location in Python | "python ip geolocation" | W1 |
| 4 | Detect VPN/Proxy from IP Address | "detect vpn proxy ip" | W1 |
| 5 | Free IP Geolocation API Guide | "free ip geolocation api" | W1 |

| 平台 | 文章数 | Week |
|------|--------|------|
| Dev.to | 5（每篇博文同步） | W1-W2 |
| Hashnode | 5（同上） | W1-W2 |
| CSDN | 1-2 | W2-W3 |
| 掘金 | 1-2 | W3 |
| 知乎 | 1-2 | W3 |
| V2EX | 1 | W3 |

---

## 每日时间预算

| 时间段 | 动作 | 耗时 |
|--------|------|------|
| 上午 | Stack Overflow 搜索 + 回答 | 30 min |
| 下午 | 博文 / Reddit / 内容创作 | 30 min |
| 晚上 | 数据检查 + 社区互动 | 10 min |
| **合计** | | **70 min/天** |

---

## 成功指标仪表盘

| 指标 | Week 1 | Week 2 | Week 3 | Week 4 | 最终 |
|------|--------|--------|--------|--------|------|
| 网站 UV/天 | 50 | 100 | 150 | 200 | 200+ |
| 免费注册累计 | 30 | 80 | 180 | 300 | **300** |
| 付费用户累计 | 0 | 2 | 5 | 10 | **10** |
| GitHub Stars | 15 | 30 | 50 | 70 | 70+ |
| SO 回答数 | 11 | 25 | 40 | 55 | 55+ |
| 博文数 | 5 | 5 | 5 | 6 | 6 |
| PyPI 下载 | 20 | 50 | 100 | 150 | 150+ |
| npm 下载 | 15 | 35 | 70 | 100 | 100+ |

---

## 第一天执行清单（6/26 明天）

```
□ 1. GitHub ipgeo 仓库 — git init + push social preview + topics
□ 2. GitHub ipgeo-python — git init + push  
□ 3. GitHub ipgeo-js — git init + push
□ 4. Awesome list PR — 找到并提交 1 个
□ 5. Stack Overflow 账号注册
□ 6. 博文 #2 "IPinfo Alternative" 草稿
```

---

*计划是活的——每周复盘根据实际数据调整。*
