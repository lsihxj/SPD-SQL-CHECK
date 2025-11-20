# SQL检查工具 - 使用手册

## 目录

1. [功能概述](#功能概述)
2. [快速开始](#快速开始)
3. [配置管理](#配置管理)
4. [SQL检查](#sql检查)
5. [历史记录](#历史记录)
6. [最佳实践](#最佳实践)

## 功能概述

SQL检查工具是一个基于AI的PostgreSQL SQL语句质量检查系统，主要功能包括：

- ✅ **多AI厂家支持** - OpenAI、Claude、通义千问、文心一言等
- ✅ **智能检查** - 语法规范、性能问题、安全隐患、最佳实践
- ✅ **性能分析** - EXPLAIN执行计划分析
- ✅ **批量处理** - 支持批量SQL检查，串行执行避免API限流
- ✅ **历史追溯** - 完整的检查记录，支持查询和导出
- ✅ **灵活配置** - AI模型、提示词、参数可自定义

## 快速开始

### 1. 访问系统

启动服务后，访问：
- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health

### 2. 首次配置

#### 步骤1：配置AI厂家

使用API或前端界面添加AI厂家配置：

```json
POST /api/config/providers
{
  "provider_name": "openai",
  "provider_display_name": "OpenAI GPT",
  "api_endpoint": "https://api.openai.com/v1",
  "api_key": "sk-your-api-key-here",
  "is_active": true
}
```

#### 步骤2：配置AI模型

添加要使用的AI模型：

```json
POST /api/config/models
{
  "provider_id": 1,
  "model_name": "gpt-4",
  "model_display_name": "GPT-4",
  "system_prompt": "你是一位资深的PostgreSQL数据库专家和SQL优化顾问。你的任务是检查SQL语句的语法规范性、性能问题、安全问题，并提供优化建议。",
  "user_prompt_template": "请检查以下PostgreSQL SQL语句：\n\nSQL语句：\n{{SQL_STATEMENT}}\n\nEXPLAIN执行计划：\n{{EXPLAIN_RESULT}}\n\n请提供详细的检查结果和优化建议。",
  "max_tokens": 4000,
  "temperature": 0.7,
  "is_default": true
}
```

#### 步骤3：配置ERP数据库（可选）

如果需要从ERP数据库获取SQL或执行EXPLAIN：

```json
POST /api/config/erp-databases
{
  "config_name": "生产ERP",
  "host": "localhost",
  "port": 5432,
  "database_name": "erp_db",
  "username": "postgres",
  "password": "password",
  "sql_query_for_sqls": "SELECT id, sql_content FROM sql_statements",
  "is_active": true
}
```

## 配置管理

### AI厂家管理

#### 查看所有AI厂家

```bash
GET /api/config/providers
```

#### 更新AI厂家

```bash
PUT /api/config/providers/{provider_id}
{
  "provider_display_name": "OpenAI GPT-4",
  "is_active": true
}
```

#### 删除AI厂家

```bash
DELETE /api/config/providers/{provider_id}
```

### AI模型管理

#### 查看所有模型

```bash
GET /api/config/models
```

#### 按厂家筛选模型

```bash
GET /api/config/models?provider_id=1
```

#### 更新模型配置

```bash
PUT /api/config/models/{model_id}
{
  "system_prompt": "更新后的系统提示词",
  "temperature": 0.5
}
```

### 提示词模板

#### 系统提示词建议

```text
你是一位资深的PostgreSQL数据库专家和SQL优化顾问。你的任务是检查SQL语句的语法规范性、性能问题、安全问题，并提供优化建议。

请按照以下维度进行检查：
1. 语法规范性：PostgreSQL语法标准、SQL编写规范、命名规范
2. 性能问题：索引使用、JOIN优化、子查询优化、LIMIT使用等
3. 安全问题：SQL注入风险、权限使用、敏感数据访问
4. 最佳实践：可读性、可维护性、扩展性建议

请以JSON格式返回检查结果，包含：
{
  "score": 0-100的评分,
  "issues": [
    {
      "type": "问题类型",
      "severity": "严重程度(high/medium/low)",
      "location": "位置",
      "description": "描述",
      "suggestion": "建议"
    }
  ],
  "optimized_sql": "优化后的SQL（如适用）",
  "performance_assessment": "性能评估"
}
```

#### 用户提示词模板变量

可用变量：
- `{{SQL_STATEMENT}}` - SQL语句
- `{{EXPLAIN_RESULT}}` - EXPLAIN执行计划
- `{{TABLE_SCHEMA}}` - 表结构信息

示例：
```text
请检查以下PostgreSQL SQL语句：

SQL语句：
{{SQL_STATEMENT}}

EXPLAIN执行计划：
{{EXPLAIN_RESULT}}

请提供详细的检查结果和优化建议。
```

## SQL检查

### 单个SQL检查

#### 基本检查

```bash
POST /api/check/single
{
  "sql_statement": "SELECT * FROM users WHERE id = 1",
  "model_id": 1
}
```

#### 带EXPLAIN结果的检查

```bash
POST /api/check/single
{
  "sql_statement": "SELECT * FROM users WHERE email = 'test@example.com'",
  "model_id": 1,
  "explain_result": "EXPLAIN结果JSON字符串"
}
```

#### 响应示例

```json
{
  "id": 1,
  "batch_id": "batch_20251117_143000_a1b2c3d4",
  "original_sql": "SELECT * FROM users WHERE id = 1",
  "check_status": "success",
  "ai_check_result": "...",
  "explain_result": "...",
  "check_duration": 1500,
  "created_at": "2025-11-17T14:30:00",
  "checked_at": "2025-11-17T14:30:01"
}
```

### 批量SQL检查

#### 发起批量检查

```bash
POST /api/check/batch
{
  "sql_statements": [
    {
      "sql": "SELECT * FROM users",
      "explain_result": null
    },
    {
      "sql": "SELECT * FROM orders WHERE user_id = 1",
      "explain_result": null
    }
  ],
  "model_id": 1
}
```

#### 响应示例

```json
{
  "batch_id": "batch_20251117_143000_a1b2c3d4",
  "total_count": 2,
  "success_count": 0,
  "failed_count": 0,
  "status": "in_progress"
}
```

#### 查询进度

```bash
GET /api/check/progress/batch_20251117_143000_a1b2c3d4
```

响应：
```json
{
  "batch_id": "batch_20251117_143000_a1b2c3d4",
  "total_count": 2,
  "completed_count": 1,
  "success_count": 1,
  "failed_count": 0,
  "progress": 50,
  "remaining_time": 1500,
  "status": "in_progress"
}
```

## 历史记录

### 查询检查记录

#### 基本查询

```bash
GET /api/history/records?limit=100&offset=0
```

#### 按批次查询

```bash
GET /api/history/records?batch_id=batch_20251117_143000_a1b2c3d4
```

#### 按状态查询

```bash
GET /api/history/records?check_status=success&limit=50
```

#### 按时间范围查询

```bash
GET /api/history/records?start_date=2025-11-01T00:00:00&end_date=2025-11-17T23:59:59
```

### 查看单个记录

```bash
GET /api/history/records/123
```

### 查询批次汇总

#### 查看所有批次

```bash
GET /api/history/summary?limit=50
```

#### 查看特定批次详情

```bash
GET /api/history/summary/batch_20251117_143000_a1b2c3d4
```

响应包含批次汇总和所有相关记录：
```json
{
  "summary": {
    "batch_id": "batch_20251117_143000_a1b2c3d4",
    "total_count": 10,
    "success_count": 8,
    "failed_count": 2,
    "start_time": "2025-11-17T14:30:00",
    "end_time": "2025-11-17T14:35:00",
    "total_duration": 300
  },
  "records": [...]
}
```

## 最佳实践

### 1. AI模型选择

| 场景 | 推荐模型 | 理由 |
|------|---------|------|
| 快速检查 | GPT-3.5 | 响应快，成本低 |
| 深度分析 | GPT-4 | 分析全面，准确度高 |
| 中文环境 | 通义千问/文心一言 | 中文理解更好 |
| 预算有限 | 国内大模型 | 成本较低 |

### 2. 批量检查策略

**小批量**（<50条SQL）：
- 适合日常检查
- 响应快速
- 便于及时发现问题

**大批量**（50-200条SQL）：
- 适合定期全面检查
- 建议选择成本较低的模型
- 在非高峰时段执行

**超大批量**（>200条SQL）：
- 分批处理
- 每批100条左右
- 避免单次检查时间过长

### 3. 提示词优化

**通用建议**：
- 明确指定输出格式（建议JSON）
- 包含检查维度说明
- 提供示例输出
- 控制提示词长度（避免超token限制）

**专项检查**：
- 性能检查：侧重EXPLAIN分析
- 安全检查：侧重SQL注入、权限
- 规范检查：侧重编码规范、命名

### 4. 结果解读

#### 严重程度分级

- **High**（高）：必须修复的问题
  - SQL注入风险
  - 大表全表扫描
  - 严重性能问题

- **Medium**（中）：建议修复的问题
  - 索引缺失
  - 查询优化建议
  - 代码规范问题

- **Low**（低）：可选优化
  - 可读性改进
  - 命名建议
  - 代码风格

#### 性能评分解读

- **90-100分**：优秀，无明显问题
- **70-89分**：良好，有小优化空间
- **50-69分**：一般，建议优化
- **<50分**：较差，需要重点优化

### 5. 常见问题处理

#### 问题1：AI检查结果不准确

**解决方案**：
1. 优化提示词，提供更多上下文
2. 提供表结构信息
3. 尝试不同的AI模型
4. 结合EXPLAIN结果

#### 问题2：批量检查失败率高

**解决方案**：
1. 检查SQL语法是否正确
2. 确认AI API配额充足
3. 降低批量大小
4. 查看具体错误信息

#### 问题3：检查速度慢

**解决方案**：
1. 选择响应更快的模型
2. 减少批量大小
3. 优化提示词长度
4. 检查网络连接

## API参考

完整的API文档请访问：http://localhost:8000/docs

主要接口：

| 接口 | 方法 | 功能 |
|------|------|------|
| /api/config/providers | GET/POST/PUT/DELETE | AI厂家管理 |
| /api/config/models | GET/POST/PUT/DELETE | AI模型管理 |
| /api/config/erp-databases | GET/POST/PUT/DELETE | ERP数据库管理 |
| /api/check/single | POST | 单个SQL检查 |
| /api/check/batch | POST | 批量SQL检查 |
| /api/check/progress/{batch_id} | GET | 查询检查进度 |
| /api/history/records | GET | 查询检查记录 |
| /api/history/summary | GET | 查询批次汇总 |

---

**手册版本：** 1.0  
**最后更新：** 2025-11-17
