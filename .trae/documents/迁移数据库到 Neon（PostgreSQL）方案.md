**目标**

* 在本地开发环境也使用同一个 Neon PostgreSQL 数据库，避免环境数据不一致。

**本地环境设置（Windows）**

* 安装驱动：pip install psycopg2-binary

* 在项目根目录创建/更新 .env：

  * DATABASE\_URL="postgresql://neondb\_owner:【你的密码】@ep-flat-mountain-ago04r9m-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require\&channel\_binding=require"

* 确保 .env 未被提交到仓库（.gitignore 生效）。

* 防火墙/网络：允许到 \*.neon.tech 的 5432/TLS 出站；家庭/办公网络一般默认允许。

**代码行为（无需额外改动）**

* server.py 已通过 dotenv 加载 .env；启动时会读取 DATABASE\_URL。

* database.py：使用 create\_engine 加载该 URL；我们将为 PostgreSQL 连接启用：

  * pool\_pre\_ping=True（防空闲断开）

  * poolclass=NullPool（适配 Serverless，减少持久连接）

  * 不额外设置 ssl（URL 已含 sslmode=require 与 channel\_binding=require）。

**表结构与兼容**

* 首次连接 Neon（空库）：metadata.create\_all(engine) 自动创建 airports、history 表及字段。

* 已有库：如果缺列，使用 Postgres 兼容 SQL 迁移：

  * ALTER TABLE history ADD COLUMN IF NOT EXISTS cost TEXT;

  * ALTER TABLE history ADD COLUMN IF NOT EXISTS price TEXT;

  * ALTER TABLE history ADD COLUMN IF NOT EXISTS data\_json TEXT;

* 保持 cost/price 为 TEXT，前端完成汇总与展示。

**验证步骤（本地）**

* 运行：python server.py

* 打开 <http://127.0.0.1:5000/>

* 执行一次翻译保存（/process），在“历史记录/已出票”中看到条目；刷新统计弹窗确认数据读写正常。

**注意事项**

* 同一数据库被本地与线上同时使用时，统计与列表将实时共享数据。

* 如需分环境隔离数据，可在 Neon 创建另一个数据库，并为本地 .env 设置不同 DATABASE\_URL。

* 由于你已公开

