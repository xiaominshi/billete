# 执行方案：环比增长指标 (Trend Indicators)

您选择了方案 2。我将为数据分析仪表盘添加环比增长显示。

## 具体步骤

1.  **后端 (`database.py`)**:
    *   修改 `get_kpi_stats(days)` 函数。
    *   在查询当前 `days` 数据的基础上，额外查询 `previous_period` (即 `2*days` 到 `days` 之间) 的数据。
    *   计算每个 KPI 的变化百分比：`((当前值 - 过去值) / 过去值) * 100`。
    *   返回结构中增加 `change_searches`, `change_pax`, `change_avg` 等字段。

2.  **后端 (`server.py`)**:
    *   `get_detailed_stats` 接口保持不变，它会自动透传 `get_kpi_stats` 返回的新字段。

3.  **前端 (`index.html`)**:
    *   修改 KPI 卡片的 HTML 结构，为每个数字旁边预留显示增长率的位置（例如 `<small id="kpi_searches_trend"></small>`）。
    *   在 `loadDetailedStats` 函数中，根据后端返回的百分比渲染箭头和颜色（正数为绿色↑，负数为红色↓）。
    *   更新翻译字典 (`translations`)，添加必要的提示文本（如果有）。

## 预期效果
*   总搜索量: **150** <span style="color:green; font-size:0.8em;">↑ 12%</span>
*   总乘客数: **320** <span style="color:red; font-size:0.8em;">↓ 5%</span>

---
**确认执行此方案？**