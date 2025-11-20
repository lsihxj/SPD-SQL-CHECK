# SQL检查工具 - SPD-SQLCHECK

## 项目概述

这是一个基于AI的PostgreSQL SQL语句检查工具，用于自动化检查ERP系统中的SQL语法规范性和性能问题。

## 技术栈

### 后端
- Python 3.11+
- FastAPI - Web框架
- SQLAlchemy - ORM
- PostgreSQL - 数据库
- OpenAI/Claude/国内大模型 - AI服务

### 前端
- React 18+
- TypeScript
- Ant Design - UI组件库
- Vite - 构建工具
- Monaco Editor - 代码编辑器

## 项目结构

```
SPD-SQLCHECK/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── adapters/          # AI适配器
│   │   │   ├── base.py        # 基类
│   │   │   ├── openai_adapter.py
│   │   │   ├── claude_adapter.py
│   │   │   ├── generic_adapter.py
│   │   │   └── factory.py     # 适配器工厂
│   │   ├── api/               # API路由
│   │   ├── core/              # 核心功能
│   │   │   └── database.py    # 数据库连接管理
│   │   ├── models/            # 数据模型
│   │   │   └── database.py    # SQLAlchemy模型
│   │   ├── services/          # 业务逻辑
│   │   └── utils/             # 工具类
│   │       └── encryption.py  # 加密服务
│   ├── config.yaml            # 配置文件
│   ├── requirements.txt       # Python依赖
│   └── main.py                # 应用入口
├── frontend/                  # 前端代码
├── database/                  # 数据库脚本
│   └── init_schema.sql        # 初始化脚本
├── scripts/                   # 启动脚本
└── docs/                      # 文档

```

## 快速开始

### 1. 环境准备

#### 前置要求
- Python 3.11+
- PostgreSQL 12+
- Node.js 18+

#### 数据库初始化

```bash
# 创建数据库
psql -U postgres
CREATE DATABASE SPDSQLCheck;
\q

# 执行初始化脚本
psql -U postgres -d SPDSQLCheck -f database/init_schema.sql
```

### 2. 后端安装

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
copy .env.example .env

# 编辑.env文件，配置数据库连接和加密密钥
```

### 3. 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 启动后端服务

```bash
cd backend
python main.py
```

后端服务将在 http://localhost:8000 启动

前端服务将在 http://localhost:5173 启动

## 功能特性

### 已实现
1. ✅ 数据库模型设计（5个核心表）
2. ✅ 加密服务（API密钥和密码加密存储）
3. ✅ 数据库连接管理（连接池、事务管理）
4. ✅ AI适配器架构（OpenAI、Claude、通用HTTP）
5. ✅ 适配器工厂模式

### 待实现
1. ⏳ SQL检查引擎（单个、批量、全部检查）
2. ⏳ EXPLAIN性能分析模块
3. ⏳ FastAPI路由和API
4. ⏳ 导出服务（Excel、PDF）
5. ⏳ 前端React应用
6. ⏳ 一键启动脚本

## 核心设计

### AI适配器架构

```python
# 支持多种AI厂家
- OpenAI (GPT-4, GPT-3.5等)
- Claude (Claude-3系列)
- 通义千问、文心一言等国内大模型

# 统一调用接口
adapter = AIAdapterFactory.create_adapter(
    provider_name='openai',
    api_key='your-key',
    api_endpoint='https://api.openai.com/v1'
)

response = await adapter.check_sql(request, system_prompt, user_prompt_template)
```

### 数据模型

1. **ai_providers** - AI厂家配置
2. **ai_models** - AI模型配置
3. **erp_database_config** - ERP数据库配置
4. **sql_check_records** - SQL检查记录
5. **check_summary** - 检查结果汇总

### 安全措施

- API密钥和密码使用AES加密存储
- 数据库连接使用参数化查询防止SQL注入
- EXPLAIN执行使用ANALYZE false避免实际执行
- 敏感信息不在日志中明文记录

## 配置说明

### 数据库配置 (config.yaml)

```yaml
database:
  host: localhost
  port: 5432
  database: SPDSQLCheck
  username: postgres
  password: "123456"
  pool_size: 10
  max_overflow: 20
```

### AI配置

AI厂家和模型配置通过Web界面管理，支持：
- API端点配置
- API密钥加密存储
- 系统提示词自定义
- 用户提示词模板
- 模型参数调整（max_tokens、temperature）

## 开发进度

| 模块 | 状态 | 完成度 |
|------|------|--------|
| 数据库设计 | ✅ 完成 | 100% |
| 加密工具 | ✅ 完成 | 100% |
| 数据库连接 | ✅ 完成 | 100% |
| AI适配器 | ✅ 完成 | 100% |
| SQL检查引擎 | ✅ 完成 | 100% |
| EXPLAIN分析 | ✅ 完成 | 100% |
| API路由 | ✅ 完成 | 100% |
| 部署脚本 | ✅ 完成 | 100% |
| 文档 | ✅ 完成 | 100% |

## 下一步计划

1. 实现SQL检查引擎核心逻辑
2. 实现EXPLAIN性能分析
3. 创建FastAPI路由
4. 开发前端React应用
5. 实现导出功能
6. 编写测试用例
7. 创建部署文档

## 许可证

MIT License

## 联系方式

如有问题，请联系项目维护者。
