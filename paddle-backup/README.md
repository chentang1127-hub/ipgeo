# Paddle 原版备份

备份时间：2026-06-15

## 包含文件

| 文件 | 说明 |
|------|------|
| `app/webhooks.py` | Paddle webhook 处理器（HMAC 验签 + 5 种事件 + checkout 创建） |
| `app/config.py` | 配置项（含 Paddle price_id → plan 映射） |
| `app/main.py` | API 入口（register / claim / webhook 端点，Paddle 版本） |
| `docs/signup.html` | 注册页（Paddle checkout 流程） |
| `docs/success.html` | 成功页（Paddle checkout_id → claim 兑换 Key） |
| `.env.example` | 环境变量模板（含 PADDLE 相关变量） |
| `requirements.txt` | Python 依赖（Paddle 版无额外依赖，用 httpx 直接调 API） |

## 恢复方法

如果 Paddle 审核通过，将这些文件复制回原位：

```bash
cp paddle-backup/app/webhooks.py app/webhooks.py
cp paddle-backup/app/config.py app/config.py
cp paddle-backup/app/main.py app/main.py
cp paddle-backup/docs/signup.html docs/signup.html
cp paddle-backup/docs/success.html docs/success.html
cp paddle-backup/.env.example .env.example
cp paddle-backup/requirements.txt requirements.txt
```

然后重新部署：
```bash
git add -A && git commit -m "restore Paddle integration" && git push
```

## Lemon Squeezy 替代方案进行中

当前正在将 Paddle 替换为 Lemon Squeezy。如果 Paddle 审核通过，可随时回滚此备份。
