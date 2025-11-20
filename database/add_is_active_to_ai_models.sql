-- 为AI模型表添加is_active字段

-- 添加is_active列（如果不存在）
ALTER TABLE ai_models 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- 为现有记录设置默认值为true
UPDATE ai_models SET is_active = TRUE WHERE is_active IS NULL;

-- 添加注释
COMMENT ON COLUMN ai_models.is_active IS '是否启用';
