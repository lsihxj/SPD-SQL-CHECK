-- SQL Check Tool Database Initialization Script
-- Database: SPDSQLCheck
-- Description: 创建SQL检查工具所需的所有表和索引

-- ============================================
-- 1. AI厂家配置表
-- ============================================
CREATE TABLE IF NOT EXISTS ai_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) NOT NULL UNIQUE,
    provider_display_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(500) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_providers IS 'AI厂家配置表';
COMMENT ON COLUMN ai_providers.provider_name IS '厂家名称（openai/claude/qwen/wenxin等）';
COMMENT ON COLUMN ai_providers.api_key IS 'API密钥（加密存储）';

-- ============================================
-- 2. AI模型配置表
-- ============================================
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    provider_id INTEGER NOT NULL REFERENCES ai_providers(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL,
    model_display_name VARCHAR(100) NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT,
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE ai_models IS 'AI模型配置表';
COMMENT ON COLUMN ai_models.system_prompt IS '系统提示词';
COMMENT ON COLUMN ai_models.user_prompt_template IS '用户提示词模板';

-- ============================================
-- 3. ERP数据库配置表
-- ============================================
CREATE TABLE IF NOT EXISTS erp_database_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL,
    host VARCHAR(200) NOT NULL,
    port INTEGER NOT NULL DEFAULT 5432,
    database_name VARCHAR(100) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(500) NOT NULL,
    sql_query_for_sqls TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE erp_database_config IS 'ERP数据库配置表';
COMMENT ON COLUMN erp_database_config.sql_query_for_sqls IS '获取SQL语句的查询语句';
COMMENT ON COLUMN erp_database_config.password IS '密码（加密存储）';

-- ============================================
-- 4. SQL检查记录表
-- ============================================
CREATE TABLE IF NOT EXISTS sql_check_records (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50),
    original_sql TEXT NOT NULL,
    sql_hash VARCHAR(64),
    check_type VARCHAR(20) NOT NULL,
    ai_model_id INTEGER REFERENCES ai_models(id) ON DELETE SET NULL,
    ai_check_result TEXT,
    explain_result TEXT,
    performance_metrics JSONB,
    check_status VARCHAR(20) NOT NULL,
    error_message TEXT,
    check_duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checked_at TIMESTAMP
);

COMMENT ON TABLE sql_check_records IS 'SQL检查记录表';
COMMENT ON COLUMN sql_check_records.batch_id IS '批次ID（批量检查时相同）';
COMMENT ON COLUMN sql_check_records.sql_hash IS 'SQL的哈希值（用于去重和索引）';
COMMENT ON COLUMN sql_check_records.check_type IS '检查类型（single/batch/all）';
COMMENT ON COLUMN sql_check_records.check_status IS '检查状态（pending/success/failed）';
COMMENT ON COLUMN sql_check_records.check_duration IS '检查耗时（毫秒）';

-- ============================================
-- 5. 检查结果汇总表
-- ============================================
CREATE TABLE IF NOT EXISTS check_summary (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(50) UNIQUE NOT NULL,
    total_count INTEGER NOT NULL,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    total_duration INTEGER,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE check_summary IS '检查结果汇总表';
COMMENT ON COLUMN check_summary.total_duration IS '总耗时（秒）';

-- ============================================
-- 6. 创建索引
-- ============================================

-- sql_check_records表索引
CREATE INDEX IF NOT EXISTS idx_sql_check_records_batch_id ON sql_check_records(batch_id);
CREATE INDEX IF NOT EXISTS idx_sql_check_records_sql_hash ON sql_check_records(sql_hash);
CREATE INDEX IF NOT EXISTS idx_sql_check_records_check_status ON sql_check_records(check_status);
CREATE INDEX IF NOT EXISTS idx_sql_check_records_created_at ON sql_check_records(created_at);
CREATE INDEX IF NOT EXISTS idx_sql_check_records_ai_model_id ON sql_check_records(ai_model_id);

-- check_summary表索引
CREATE INDEX IF NOT EXISTS idx_check_summary_batch_id ON check_summary(batch_id);
CREATE INDEX IF NOT EXISTS idx_check_summary_start_time ON check_summary(start_time);

-- ai_models表索引
CREATE INDEX IF NOT EXISTS idx_ai_models_provider_id ON ai_models(provider_id);
CREATE INDEX IF NOT EXISTS idx_ai_models_is_default ON ai_models(is_default);

-- ai_providers表索引
CREATE INDEX IF NOT EXISTS idx_ai_providers_is_active ON ai_providers(is_active);

-- erp_database_config表索引
CREATE INDEX IF NOT EXISTS idx_erp_database_config_is_active ON erp_database_config(is_active);

-- ============================================
-- 7. 创建触发器函数：自动更新updated_at字段
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要的表创建触发器
DROP TRIGGER IF EXISTS update_ai_providers_updated_at ON ai_providers;
CREATE TRIGGER update_ai_providers_updated_at
    BEFORE UPDATE ON ai_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ai_models_updated_at ON ai_models;
CREATE TRIGGER update_ai_models_updated_at
    BEFORE UPDATE ON ai_models
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_erp_database_config_updated_at ON erp_database_config;
CREATE TRIGGER update_erp_database_config_updated_at
    BEFORE UPDATE ON erp_database_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 8. 插入默认数据
-- ============================================

-- 插入示例AI厂家配置（需要用户配置实际的API密钥）
INSERT INTO ai_providers (provider_name, provider_display_name, api_endpoint, api_key, is_active)
VALUES 
    ('openai', 'OpenAI', 'https://api.openai.com/v1', 'YOUR_API_KEY_HERE', FALSE),
    ('claude', 'Anthropic Claude', 'https://api.anthropic.com', 'YOUR_API_KEY_HERE', FALSE)
ON CONFLICT (provider_name) DO NOTHING;

-- 插入示例AI模型配置
INSERT INTO ai_models (provider_id, model_name, model_display_name, system_prompt, user_prompt_template, max_tokens, temperature, is_default)
VALUES 
    (
        (SELECT id FROM ai_providers WHERE provider_name = 'openai' LIMIT 1),
        'gpt-4',
        'GPT-4',
        '你是一位资深的PostgreSQL数据库专家和SQL优化顾问。你的任务是检查SQL语句的语法规范性、性能问题、安全问题，并提供优化建议。请按照以下维度进行检查：
1. 语法规范性：PostgreSQL语法标准、SQL编写规范、命名规范
2. 性能问题：索引使用、JOIN优化、子查询优化、LIMIT使用等
3. 安全问题：SQL注入风险、权限使用、敏感数据访问
4. 最佳实践：可读性、可维护性、扩展性建议

请以JSON格式返回检查结果，包含：
{
  "score": 0-100的评分,
  "issues": [{"type": "问题类型", "severity": "严重程度(high/medium/low)", "location": "位置", "description": "描述", "suggestion": "建议"}],
  "optimized_sql": "优化后的SQL（如适用）",
  "performance_assessment": "性能评估"
}',
        '请检查以下PostgreSQL SQL语句：

SQL语句：
{{SQL_STATEMENT}}

EXPLAIN执行计划：
{{EXPLAIN_RESULT}}

请提供详细的检查结果和优化建议。',
        4000,
        0.7,
        TRUE
    )
ON CONFLICT DO NOTHING;

-- 插入示例ERP数据库配置
INSERT INTO erp_database_config (config_name, host, port, database_name, username, password, sql_query_for_sqls, is_active)
VALUES 
    (
        '本地ERP数据库示例',
        'localhost',
        5432,
        'erp_database_name',
        'postgres',
        'ENCRYPTED_PASSWORD_PLACEHOLDER',
        'SELECT id, sql_content FROM sql_statements WHERE status = ''active''',
        FALSE
    )
ON CONFLICT DO NOTHING;

-- ============================================
-- 完成初始化
-- ============================================
SELECT 'Database initialization completed successfully!' AS status;
