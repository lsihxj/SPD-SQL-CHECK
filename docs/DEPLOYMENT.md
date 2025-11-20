# SQL检查工具 - 部署指南

## 系统要求

### 必需软件
- Python 3.11 或更高版本
- PostgreSQL 12 或更高版本
- Windows 10/11 或 Linux/MacOS

### 推荐配置
- CPU: 4核心以上
- 内存: 8GB以上
- 硬盘: 10GB可用空间

## 快速部署

### 方法1：使用自动安装脚本（推荐Windows用户）

1. 打开PowerShell（以管理员身份）
2. 执行安装脚本：
```powershell
cd SPD-SQLCHECK
.\scripts\setup.ps1
```

3. 按照提示完成安装和数据库初始化

### 方法2：手动部署

#### 步骤1：数据库准备

```bash
# 连接PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE SPDSQLCheck;
\q

# 执行初始化脚本
psql -U postgres -d SPDSQLCheck -f database/init_schema.sql
```

#### 步骤2：安装后端依赖

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 步骤3：配置环境变量

复制 `.env.example` 为 `.env` 并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=SPDSQLCheck
DATABASE_USER=postgres
DATABASE_PASSWORD=123456

# 加密密钥（请修改为强密码！）
ENCRYPTION_KEY=your-very-long-and-secure-32-character-key-here
SECRET_KEY=your-secret-key-for-jwt-tokens-change-this

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

#### 步骤4：启动服务

```bash
# 确保虚拟环境已激活
python main.py
```

服务将在 http://localhost:8000 启动

## 配置说明

### 1. AI厂家配置

在启动服务后，访问 http://localhost:8000/docs 使用API配置AI厂家。

#### 添加OpenAI配置

```bash
POST /api/config/providers
{
  "provider_name": "openai",
  "provider_display_name": "OpenAI",
  "api_endpoint": "https://api.openai.com/v1",
  "api_key": "sk-your-openai-api-key",
  "is_active": true
}
```

#### 添加AI模型

```bash
POST /api/config/models
{
  "provider_id": 1,
  "model_name": "gpt-4",
  "model_display_name": "GPT-4",
  "system_prompt": "你是一位资深的PostgreSQL数据库专家...",
  "user_prompt_template": "请检查以下SQL语句：\n{{SQL_STATEMENT}}",
  "max_tokens": 4000,
  "temperature": 0.7,
  "is_default": true
}
```

### 2. ERP数据库配置

#### 添加ERP数据库连接

```bash
POST /api/config/erp-databases
{
  "config_name": "生产环境ERP",
  "host": "localhost",
  "port": 5432,
  "database_name": "erp_production",
  "username": "postgres",
  "password": "your-password",
  "sql_query_for_sqls": "SELECT id, sql_content FROM sql_statements WHERE status = 'active'",
  "is_active": true
}
```

## 使用说明

### 1. 单个SQL检查

```bash
POST /api/check/single
{
  "sql_statement": "SELECT * FROM users WHERE id = 1",
  "model_id": 1,
  "explain_result": null
}
```

### 2. 批量SQL检查

```bash
POST /api/check/batch
{
  "sql_statements": [
    {"sql": "SELECT * FROM users", "explain_result": null},
    {"sql": "SELECT * FROM orders WHERE user_id = 1", "explain_result": null}
  ],
  "model_id": 1
}
```

### 3. 查询检查进度

```bash
GET /api/check/progress/{batch_id}
```

### 4. 查看历史记录

```bash
GET /api/history/records?limit=100&offset=0
```

## 常见问题

### Q1: 启动失败，提示数据库连接错误

**解决方案：**
1. 确认PostgreSQL服务已启动
2. 检查 `.env` 文件中的数据库配置是否正确
3. 确认SPDSQLCheck数据库已创建

### Q2: AI检查失败

**解决方案：**
1. 检查AI厂家配置的API密钥是否正确
2. 确认网络连接正常，能访问AI服务API
3. 查看后端日志获取详细错误信息

### Q3: 加密密钥配置错误

**解决方案：**
1. 确保 `ENCRYPTION_KEY` 至少32个字符
2. 重新生成密钥：使用随机字符串生成器
3. 如果修改了密钥，需要重新配置所有API密钥和密码

## 性能优化建议

### 1. 数据库优化
- 为常用查询字段创建索引
- 定期清理旧的检查记录
- 配置合适的连接池大小

### 2. 批量检查优化
- 控制单批次SQL数量（建议不超过100条）
- 选择合适的AI模型（平衡速度和质量）
- 避免在高峰时段执行大批量检查

### 3. 缓存配置
- 启用AI检查结果缓存（相同SQL避免重复检查）
- 配置合理的缓存过期时间

## 安全建议

1. **修改默认密钥**：务必修改 `.env` 中的加密密钥和密钥
2. **限制网络访问**：配置防火墙，只允许必要的IP访问
3. **使用HTTPS**：生产环境建议配置SSL证书
4. **定期备份**：定期备份SPDSQLCheck数据库
5. **权限控制**：为不同用户设置不同的访问权限（需额外开发）

## 更新升级

### 更新依赖包

```bash
cd backend
pip install --upgrade -r requirements.txt
```

### 数据库迁移

如果有新的数据库schema变更：

```bash
# 备份数据库
pg_dump -U postgres SPDSQLCheck > backup.sql

# 执行迁移脚本
psql -U postgres -d SPDSQLCheck -f database/migrations/xxx.sql
```

## 故障排查

### 查看日志

后端日志位置：`backend/logs/app.log`

### 调试模式

编辑 `config.yaml`，设置：
```yaml
server:
  log_level: debug
```

### 数据库连接测试

```python
# 在Python环境中测试
from app.core.database import init_database, get_db_manager

database_url = "postgresql://postgres:123456@localhost:5432/SPDSQLCheck"
init_database(database_url)

db_manager = get_db_manager()
print("数据库连接成功！")
```

## 技术支持

如遇问题，请提供：
1. 错误日志
2. 系统环境信息（OS、Python版本、PostgreSQL版本）
3. 详细的错误复现步骤

---

**文档版本：** 1.0  
**最后更新：** 2025-11-17
