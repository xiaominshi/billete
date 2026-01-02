# 执行方案：客户回头率分析 (Repeat Customer Analysis)

您决定只执行 **客户回头率分析**。

## 具体步骤

1.  **后端 (`database.py`)**:
    *   创建 `get_repeat_customer_stats(limit=5)` 函数。
    *   扫描全量历史数据的 `passenger_info` 字段。
    *   清洗并统计每个乘客姓名的出现频次。
    *   返回：
        *   `repeat_rate`: 复购率 (百分比)。
        *   `new_vs_returning`: 新客与老客的数量分布。
        *   `top_customers`: 出现频次最高的 5 位乘客姓名及次数。

2.  **后端 (`server.py`)**:
    *   更新 `/stats/detailed` 接口，调用上述新函数并将结果包含在 JSON 响应中。

3.  **前端 (`index.html`)**:
    *   在统计弹窗的底部或侧边添加 **"客户分析 (Customer Insights)"** 区域。
    *   **左侧**: 显示 "复购率" 大数字 KPI。
    *   **中间**: 绘制一个饼图 (New vs Returning)。
    *   **右侧**: 一个小表格列出 Top 5 忠实客户。
    *   更新翻译字典 (`translations`) 支持多语言。

---
**确认执行？**