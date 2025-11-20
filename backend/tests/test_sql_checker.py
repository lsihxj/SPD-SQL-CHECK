"""
SQL检查引擎单元测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.sql_checker import SQLCheckEngine
from app.models.database import SQLCheckRecord, CheckSummary


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.query = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def sql_checker(mock_db_session):
    """创建SQL检查引擎实例"""
    with patch('app.services.sql_checker.get_encryption_service'):
        return SQLCheckEngine(mock_db_session)


def test_generate_batch_id(sql_checker):
    """测试批次ID生成"""
    batch_id = sql_checker._generate_batch_id()
    
    assert batch_id.startswith('batch_')
    assert len(batch_id) > 20  # batch_ + timestamp + _ + uuid


def test_calculate_sql_hash(sql_checker):
    """测试SQL哈希计算"""
    sql1 = "SELECT * FROM users"
    sql2 = "SELECT * FROM users"
    sql3 = "SELECT * FROM orders"
    
    hash1 = sql_checker._calculate_sql_hash(sql1)
    hash2 = sql_checker._calculate_sql_hash(sql2)
    hash3 = sql_checker._calculate_sql_hash(sql3)
    
    # 相同SQL应该有相同哈希
    assert hash1 == hash2
    # 不同SQL应该有不同哈希
    assert hash1 != hash3
    # 哈希长度应该是64（SHA256）
    assert len(hash1) == 64


@pytest.mark.asyncio
async def test_check_single_success(sql_checker, mock_db_session):
    """测试单个SQL检查成功"""
    # 模拟数据库查询
    mock_model = Mock()
    mock_model.id = 1
    mock_model.provider = Mock()
    mock_model.provider.provider_name = 'openai'
    mock_model.provider.api_key = 'encrypted_key'
    mock_model.provider.api_endpoint = 'https://api.openai.com/v1'
    mock_model.system_prompt = 'You are a SQL checker'
    mock_model.user_prompt_template = 'Check this SQL: {sql}'
    mock_model.max_tokens = 4000
    mock_model.temperature = 0.7
    mock_model.model_name = 'gpt-4'
    
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_model
    
    # 模拟AI响应
    mock_response = Mock()
    mock_response.success = True
    mock_response.result = 'SQL is valid'
    mock_response.error = None
    
    with patch('app.services.sql_checker.AIAdapterFactory.create_adapter') as mock_factory:
        mock_adapter = AsyncMock()
        mock_adapter.check_sql = AsyncMock(return_value=mock_response)
        mock_factory.return_value = mock_adapter
        
        with patch('app.services.sql_checker.get_encryption_service') as mock_encrypt:
            mock_encrypt.return_value.decrypt.return_value = 'decrypted_key'
            
            # 执行检查
            result = await sql_checker.check_single(
                sql_statement="SELECT * FROM users",
                model_id=1
            )
            
            # 验证结果
            assert result is not None
            assert mock_db_session.add.called
            assert mock_db_session.commit.called


def test_get_batch_progress(sql_checker, mock_db_session):
    """测试获取批次进度"""
    # 模拟汇总数据
    mock_summary = Mock()
    mock_summary.batch_id = 'test_batch'
    mock_summary.total_count = 10
    mock_summary.success_count = 7
    mock_summary.failed_count = 3
    mock_summary.total_duration = 100
    
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_summary
    
    # 获取进度
    progress = sql_checker.get_batch_progress('test_batch')
    
    # 验证
    assert progress['batch_id'] == 'test_batch'
    assert progress['total_count'] == 10
    assert progress['completed_count'] == 10
    assert progress['success_count'] == 7
    assert progress['failed_count'] == 3
    assert progress['progress'] == 100
    assert progress['status'] == 'completed'


def test_get_batch_progress_not_found(sql_checker, mock_db_session):
    """测试批次不存在"""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None
    
    # 应该抛出异常
    with pytest.raises(ValueError, match="Batch .* not found"):
        sql_checker.get_batch_progress('nonexistent_batch')
