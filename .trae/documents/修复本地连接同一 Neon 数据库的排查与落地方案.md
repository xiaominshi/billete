**目标**

* 本地与 Render 使用同一 Neon 数据库实例，数据完全一致。

**快速排查与验证**

* 打开本地 <http://127.0.0.1:5000/db/health：若返回> {"dialect":"postgresql","ok":true} 则已连数据库；若不是，继续下面修复。

* 在 Neon 控制台执行 SELECT count(\*) FROM airports; 与本地页面“机场代码管理”显示数量对比，确认是否同库。

**本地环境修复步骤**

* 安装驱动：pip install psycopg2-binary。

* 配置 .env（在运行目录可被加载的位置，例如 billetepython 或项目根）：

  * DATABASE\_URL=postgresql://neondb\_owner:【你的密码】@ep-flat-mountain-ago04r9m-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require

  * 说明：如遇 channel\_binding=require 导致 libpq 兼容问题，先仅保留 sslmode=require；Render/psql 可继续使用 channel\_binding=require。

* 启动方式（确保 .env 被读取）：

  * 方案A：在项目根或 billetepython 目录运行 python server.py。

  * 方案B（显式设置）：在 PowerShell 先设置环境变量，再运行服务：

    * $env:DATABASE\_URL="postgresql://neondb\_owner:\*\*\*@ep-flat-mountain-ago04r9m-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"; python billetepython/server.py

**一致性核验**

* 本地调用 POST /airports 添加一条测试记录，例如 {"code":"ZZZ","name":"TestName"}；在 Render 访问 GET /airports 能看到同一记录（反向再测一次）。

* 本地执行一次“开始翻译”，在 Neon 的 history 表能看到新增条目；Render 的历史记录也出现同条。

**增强与可视化（待你确认后实施）**

* 新增 /db/info 返回当前连接主机名（脱敏，不含账户密码），便于肉眼确认是否指向相同 pooler。

* 在页面提示当前数据库连接状态（PostgreSQL/SQLite），一目了然。

**注意事项**

* 必须确保 .env 的 DATABASE\_URL 与 Render 完全一致（同一 host、数据库名、参数）。

* 从其他目录启动时，load\_dotenv 可能找不到 .env；建议在可被加载的位置存放 .env 或使用方案B显式设置。

* 如果 /db/health 显示 sqlite 或 ok=false，就是没有连上 Neon；按上述步骤修复。

确认后，我将：

* 应用上述 .env/驱动/启动方式，完成本地连通验证，并提供 /db/info 辅助确认（不泄漏凭证）。

