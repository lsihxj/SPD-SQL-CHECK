"""
SQL检查引擎
实现单个、批量和全部检查逻辑
"""
import hashlib
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.database import SQLCheckRecord, CheckSummary, AIModel, AIProvider, ERPDatabaseConfig
from app.adapters import AIAdapterFactory, AICheckRequest, AICheckResponse
from app.utils.encryption import get_encryption_service
from app.core.database import get_or_create_erp_connection
from app.services.explain_analyzer import ExplainAnalyzer


class SQLCheckEngine:
    """SQL检查引擎"""
    
    def __init__(self, db_session: Session):
        """
        初始化SQL检查引擎
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.encryption = get_encryption_service()
    
    def _generate_batch_id(self) -> str:
        """生成批次ID"""
        return f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _calculate_sql_hash(self, sql: str) -> str:
        """计算SQL哈希值"""
        return hashlib.sha256(sql.encode()).hexdigest()
    
    async def check_single(
        self,
        sql_statement: str,
        model_id: int,
        explain_result: Optional[str] = None,
        erp_config_id: Optional[int] = None
    ) -> SQLCheckRecord:
        """
        检查单个SQL语句
        
        Args:
            sql_statement: SQL语句
            model_id: AI模型ID
            explain_result: EXPLAIN结果（可选）
            erp_config_id: ERP数据库配置ID（用于自动执行EXPLAIN）
            
        Returns:
            检查记录
        """
        # 创建批次ID
        batch_id = self._generate_batch_id()
        
        # 创建检查记录
        record = SQLCheckRecord(
            batch_id=batch_id,
            original_sql=sql_statement,
            sql_hash=self._calculate_sql_hash(sql_statement),
            check_type='single',
            ai_model_id=model_id,
            check_status='pending',
            created_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()
        
        # 创建批次汇总
        summary = CheckSummary(
            batch_id=batch_id,
            total_count=1,
            success_count=0,
            failed_count=0,
            start_time=datetime.now()
        )
        self.db.add(summary)
        self.db.commit()
        
        # 如果没有提供EXPLAIN结果且提供了ERP配置，自动执行EXPLAIN
        if not explain_result and erp_config_id:
            explain_result = await self._execute_explain(erp_config_id, sql_statement)
            if explain_result:
                record.explain_result = explain_result
                
                # 解析EXPLAIN结果并提取性能指标
                analyzer = ExplainAnalyzer(None)  # 不需要连接对象来解析
                parsed = analyzer.parse_explain_result(explain_result)
                if 'metrics' in parsed:
                    record.performance_metrics = parsed
                self.db.commit()
        
        # 执行检查
        start_time = datetime.now()
        
        try:
            # 获取AI模型配置
            model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
            if not model:
                raise ValueError(f"AI模型(ID:{model_id})未找到，请检查配置")
            
            provider = model.provider
            if not provider:
                raise ValueError(f"AI模型'{model.model_display_name}'的发布商配置未找到")
            
            # 解密API密钥
            try:
                api_key = self.encryption.decrypt(provider.api_key)
            except Exception as decrypt_error:
                raise ValueError(f"AI发布商'{provider.provider_display_name}'的API密钥解密失败：{str(decrypt_error)}。请检查加密配置是否正确。")
            
            # 创建AI适配器
            adapter = AIAdapterFactory.create_adapter(
                provider_name=provider.provider_name,
                api_key=api_key,
                api_endpoint=provider.api_endpoint
            )
            
            # 构建检查请求
            request = AICheckRequest(
                sql_statement=sql_statement,
                explain_result=explain_result or record.explain_result
            )
            
            # 调用AI检查
            try:
                response: AICheckResponse = await adapter.check_sql(
                    request=request,
                    system_prompt=model.system_prompt or "",
                    user_prompt_template=model.user_prompt_template or "",
                    max_tokens=model.max_tokens,
                    temperature=float(model.temperature) if model.temperature else 0.7,
                    model_name=model.model_name
                )
            except Exception as ai_error:
                raise ValueError(f"AI检查调用失败：{str(ai_error)}。请检查API密钥是否有效、网络连接是否正常。")
            
            # 计算耗时
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 更新检查记录
            if response.success:
                record.check_status = 'success'
                record.ai_check_result = response.result
                record.check_duration = duration
                record.checked_at = datetime.now()
                
                # 更新汇总
                summary.success_count = 1
            else:
                record.check_status = 'failed'
                record.error_message = response.error
                record.check_duration = duration
                record.checked_at = datetime.now()
                
                # 更新汇总
                summary.failed_count = 1
            
            # 更新汇总结束时间
            summary.end_time = datetime.now()
            summary.total_duration = int((summary.end_time - summary.start_time).total_seconds())
            
            self.db.commit()
            self.db.refresh(record)
            
            return record
            
        except Exception as e:
            # 记录错误 - 提供详细信息
            error_type = type(e).__name__
            error_detail = str(e)
            
            # 构建详细错误信息
            if "decrypt" in error_detail.lower():
                full_error = f"[解密错误] {error_detail}"
            elif "api" in error_detail.lower() or "key" in error_detail.lower():
                full_error = f"[API调用错误] {error_detail}"
            elif "network" in error_detail.lower() or "connection" in error_detail.lower():
                full_error = f"[网络错误] {error_detail}"
            else:
                full_error = f"[{error_type}] {error_detail}"
            
            record.check_status = 'failed'
            record.error_message = full_error
            record.check_duration = int((datetime.now() - start_time).total_seconds() * 1000)
            record.checked_at = datetime.now()
            
            summary.failed_count = 1
            summary.end_time = datetime.now()
            summary.total_duration = int((summary.end_time - summary.start_time).total_seconds())
            
            self.db.commit()
            self.db.refresh(record)
            
            return record
    
    async def check_single_stream(
        self,
        sql_statement: str,
        model_id: int,
        explain_result: Optional[str] = None,
        erp_config_id: Optional[int] = None
    ):
        """
        检查单个SQL语句（流式输出）
        
        Args:
            sql_statement: SQL语句
            model_id: AI模型ID
            explain_result: EXPLAIN结果（可选）
            erp_config_id: ERP数据库配置ID（用于自动执行EXPLAIN）
            
        Yields:
            流式数据块（SSE格式）
        """
        import json
        
        # 创建批次ID
        batch_id = self._generate_batch_id()
        
        # 创建检查记录
        record = SQLCheckRecord(
            batch_id=batch_id,
            original_sql=sql_statement,
            sql_hash=self._calculate_sql_hash(sql_statement),
            check_type='single',
            ai_model_id=model_id,
            check_status='pending',
            created_at=datetime.now()
        )
        self.db.add(record)
        self.db.commit()
        record_id = record.id
        
        # 创建批次汇总
        summary = CheckSummary(
            batch_id=batch_id,
            total_count=1,
            success_count=0,
            failed_count=0,
            start_time=datetime.now()
        )
        self.db.add(summary)
        self.db.commit()
        
        try:
            # 如果没有提供EXPLAIN结果且提供了ERP配置，自动执行EXPLAIN
            if not explain_result and erp_config_id:
                yield f"data: {{\"type\": \"status\", \"message\": \"正在执行EXPLAIN分析...\"}}\n\n"
                explain_result = await self._execute_explain(erp_config_id, sql_statement)
                if explain_result:
                    record.explain_result = explain_result
                    
                    # 解析EXPLAIN结果并提取性能指标
                    analyzer = ExplainAnalyzer(None)
                    parsed = analyzer.parse_explain_result(explain_result)
                    if 'metrics' in parsed:
                        record.performance_metrics = parsed
                    self.db.commit()
                    
                    # 发送EXPLAIN结果
                    explain_data = json.dumps({"type": "explain", "explain_result": explain_result}, ensure_ascii=False)
                    yield f"data: {explain_data}\n\n"
                    yield f"data: {{\"type\": \"status\", \"message\": \"EXPLAIN分析完成\"}}\n\n"
            
            yield f"data: {{\"type\": \"status\", \"message\": \"正在调用AI模型检查SQL...\"}}\n\n"
            
            # 获取AI模型配置
            model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
            if not model:
                raise ValueError(f"AI模型(ID:{model_id})未找到，请检查配置")
            
            provider = model.provider
            if not provider:
                raise ValueError(f"AI模型'{model.model_display_name}'的发布商配置未找到")
            
            # 解密API密钥
            try:
                api_key = self.encryption.decrypt(provider.api_key)
            except Exception as decrypt_error:
                raise ValueError(f"AI发布商'{provider.provider_display_name}'的API密钥解密失败：{str(decrypt_error)}。请检查加密配置是否正确。")
            
            # 创建AI适配器
            adapter = AIAdapterFactory.create_adapter(
                provider_name=provider.provider_name,
                api_key=api_key,
                api_endpoint=provider.api_endpoint
            )
            
            # 构建AI检查请求
            from app.adapters.base import AICheckRequest
            request = AICheckRequest(
                sql_statement=sql_statement,
                explain_result=explain_result or record.explain_result
            )
            
            # 检查适配器是否支持流式
            if not hasattr(adapter, 'check_sql_stream'):
                yield f"data: {{\"type\": \"error\", \"message\": \"当前AI适配器不支持流式输出\"}}\n\n"
                return
            
            # 发送流式开始信号
            yield f"data: {{\"type\": \"start\", \"record_id\": {record_id}}}\n\n"
            
            # 调用AI流式检查
            start_time = datetime.now()
            full_result = ""
            
            async for chunk in adapter.check_sql_stream(
                request=request,
                system_prompt=model.system_prompt or "",
                user_prompt_template=model.user_prompt_template or "",
                max_tokens=model.max_tokens,
                temperature=float(model.temperature) if model.temperature else 0.7,
                model_name=model.model_name
            ):
                full_result += chunk
                # 发送内容块
                chunk_data = json.dumps({"type": "content", "chunk": chunk}, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
            
            # 计算耗时
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 更新检查记录
            record.check_status = 'success'
            record.ai_check_result = full_result
            record.check_duration = duration
            record.checked_at = datetime.now()
            summary.success_count = 1
            summary.end_time = datetime.now()
            summary.total_duration = int((summary.end_time - summary.start_time).total_seconds())
            self.db.commit()
            
            # 发送完成信号
            yield f"data: {{\"type\": \"done\", \"record_id\": {record_id}, \"duration\": {duration}}}\n\n"
            
        except Exception as e:
            # 记录错误
            error_type = type(e).__name__
            error_detail = str(e)
            
            # 构建详细错误信息
            if "decrypt" in error_detail.lower():
                full_error = f"[解密错误] {error_detail}"
            elif "api" in error_detail.lower() or "key" in error_detail.lower():
                full_error = f"[API调用错误] {error_detail}"
            elif "network" in error_detail.lower() or "connection" in error_detail.lower():
                full_error = f"[网络错误] {error_detail}"
            else:
                full_error = f"[{error_type}] {error_detail}"
            
            record.check_status = 'failed'
            record.error_message = full_error
            record.checked_at = datetime.now()
            summary.failed_count = 1
            summary.end_time = datetime.now()
            summary.total_duration = int((summary.end_time - summary.start_time).total_seconds())
            self.db.commit()
            
            # 发送错误信号
            error_data = json.dumps({"type": "error", "message": full_error}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    async def _execute_explain(self, erp_config_id: int, sql: str) -> Optional[str]:
        """
        执行EXPLAIN分析
        
        Args:
            erp_config_id: ERP数据库配置ID
            sql: SQL语句
            
        Returns:
            EXPLAIN结果
        """
        try:
            # 获取ERP数据库配置
            erp_config = self.db.query(ERPDatabaseConfig).filter(
                ERPDatabaseConfig.id == erp_config_id
            ).first()
            
            if not erp_config:
                return None
            
            # 解密密码
            password = self.encryption.decrypt(erp_config.password)
            
            # 创建数据库连接
            erp_conn = get_or_create_erp_connection(
                config_id=erp_config_id,
                host=erp_config.host,
                port=erp_config.port,
                database=erp_config.database_name,
                username=erp_config.username,
                password=password
            )
            
            # 执行EXPLAIN
            analyzer = ExplainAnalyzer(erp_conn)
            return analyzer.execute_explain(sql)
            
        except Exception as e:
            return f"EXPLAIN执行失败: {str(e)}"
    
    async def check_batch(
        self,
        sql_statements: List[Dict[str, Any]],
        model_id: int,
        erp_config_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量检查SQL语句（串行执行）
        
        Args:
            sql_statements: SQL语句列表，每项包含 {sql, explain_result}
            model_id: AI模型ID
            erp_config_id: ERP数据库配置ID（用于自动执行EXPLAIN）
            
        Returns:
            批次信息和进度
        """
        # 创建批次ID
        batch_id = self._generate_batch_id()
        
        # 创建批次汇总
        summary = CheckSummary(
            batch_id=batch_id,
            total_count=len(sql_statements),
            success_count=0,
            failed_count=0,
            start_time=datetime.now()
        )
        self.db.add(summary)
        self.db.commit()
        
        # 创建所有检查记录（状态为pending）
        records = []
        for sql_data in sql_statements:
            record = SQLCheckRecord(
                batch_id=batch_id,
                original_sql=sql_data['sql'],
                sql_hash=self._calculate_sql_hash(sql_data['sql']),
                check_type='batch',
                ai_model_id=model_id,
                check_status='pending',
                created_at=datetime.now()
            )
            self.db.add(record)
            records.append(record)
        
        self.db.commit()
        
        # 获取AI模型配置（只查询一次）
        model = self.db.query(AIModel).filter(AIModel.id == model_id).first()
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        provider = model.provider
        api_key = self.encryption.decrypt(provider.api_key)
        
        # 创建AI适配器（只创建一次）
        adapter = AIAdapterFactory.create_adapter(
            provider_name=provider.provider_name,
            api_key=api_key,
            api_endpoint=provider.api_endpoint
        )
        
        # 串行执行检查
        for idx, (sql_data, record) in enumerate(zip(sql_statements, records)):
            start_time = datetime.now()
            
            try:
                # 如果没有提供EXPLAIN结果且提供了ERP配置，自动执行EXPLAIN
                explain_result = sql_data.get('explain_result')
                if not explain_result and erp_config_id:
                    explain_result = await self._execute_explain(erp_config_id, sql_data['sql'])
                    if explain_result:
                        record.explain_result = explain_result
                        
                        # 解析EXPLAIN结果并提取性能指标
                        analyzer = ExplainAnalyzer(None)
                        parsed = analyzer.parse_explain_result(explain_result)
                        if 'metrics' in parsed:
                            record.performance_metrics = parsed
                        self.db.commit()
                
                # 构建检查请求
                request = AICheckRequest(
                    sql_statement=sql_data['sql'],
                    explain_result=explain_result
                )
                
                # 调用AI检查
                response: AICheckResponse = await adapter.check_sql(
                    request=request,
                    system_prompt=model.system_prompt or "",
                    user_prompt_template=model.user_prompt_template or "",
                    max_tokens=model.max_tokens,
                    temperature=float(model.temperature) if model.temperature else 0.7,
                    model_name=model.model_name
                )
                
                # 计算耗时
                duration = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # 更新检查记录
                if response.success:
                    record.check_status = 'success'
                    record.ai_check_result = response.result
                    record.check_duration = duration
                    record.checked_at = datetime.now()
                    
                    summary.success_count += 1
                else:
                    record.check_status = 'failed'
                    record.error_message = response.error
                    record.check_duration = duration
                    record.checked_at = datetime.now()
                    
                    summary.failed_count += 1
                
                self.db.commit()
                
            except Exception as e:
                # 记录错误
                record.check_status = 'failed'
                record.error_message = str(e)
                record.check_duration = int((datetime.now() - start_time).total_seconds() * 1000)
                record.checked_at = datetime.now()
                
                summary.failed_count += 1
                self.db.commit()
        
        # 更新汇总结束时间
        summary.end_time = datetime.now()
        summary.total_duration = int((summary.end_time - summary.start_time).total_seconds())
        self.db.commit()
        
        return {
            'batch_id': batch_id,
            'total_count': summary.total_count,
            'success_count': summary.success_count,
            'failed_count': summary.failed_count,
            'status': 'completed'
        }
    
    def get_batch_progress(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批次检查进度
        
        Args:
            batch_id: 批次ID
            
        Returns:
            进度信息
        """
        summary = self.db.query(CheckSummary).filter(
            CheckSummary.batch_id == batch_id
        ).first()
        
        if not summary:
            raise ValueError(f"Batch {batch_id} not found")
        
        # 统计已完成数量
        completed_count = summary.success_count + summary.failed_count
        
        # 计算进度百分比
        progress = int((completed_count / summary.total_count) * 100) if summary.total_count > 0 else 0
        
        # 估算剩余时间
        remaining_time = None
        if completed_count > 0 and summary.total_duration:
            avg_time_per_sql = summary.total_duration / completed_count
            remaining_count = summary.total_count - completed_count
            remaining_time = int(avg_time_per_sql * remaining_count)
        
        return {
            'batch_id': batch_id,
            'total_count': summary.total_count,
            'completed_count': completed_count,
            'success_count': summary.success_count,
            'failed_count': summary.failed_count,
            'progress': progress,
            'remaining_time': remaining_time,
            'status': 'completed' if completed_count == summary.total_count else 'in_progress'
        }
    
    async def check_all_from_erp(
        self,
        erp_config_id: int,
        model_id: int,
        auto_explain: bool = True
    ) -> Dict[str, Any]:
        """
        从ERP数据库获取所有SQL并批量检查
        
        Args:
            erp_config_id: ERP数据库配置ID
            model_id: AI模型ID
            auto_explain: 是否自动执行EXPLAIN分析
            
        Returns:
            批次信息
        """
        # 获取ERP数据库配置
        erp_config = self.db.query(ERPDatabaseConfig).filter(
            ERPDatabaseConfig.id == erp_config_id
        ).first()
        
        if not erp_config:
            raise ValueError(f"ERP database config {erp_config_id} not found")
        
        # 解密密码
        password = self.encryption.decrypt(erp_config.password)
        
        # 创建数据库连接
        erp_conn = get_or_create_erp_connection(
            config_id=erp_config_id,
            host=erp_config.host,
            port=erp_config.port,
            database=erp_config.database_name,
            username=erp_config.username,
            password=password
        )
        
        # 测试连接
        if not erp_conn.test_connection():
            raise ValueError(f"Failed to connect to ERP database")
        
        # 执行查询获取所有SQL语句
        sql_list = []
        try:
            with erp_conn.get_cursor() as cursor:
                cursor.execute(erp_config.sql_query_for_sqls)
                rows = cursor.fetchall()
                
                # 假设查询返回的是SQL语句列表
                for row in rows:
                    sql_statement = row[0] if isinstance(row, tuple) else row
                    if sql_statement:
                        sql_list.append({'sql': sql_statement})
        
        except Exception as e:
            raise ValueError(f"Failed to fetch SQL statements from ERP database: {str(e)}")
        
        if not sql_list:
            raise ValueError("No SQL statements found in ERP database")
        
        # 调用批量检查（如果启用自动EXPLAIN，传递erp_config_id）
        return await self.check_batch(
            sql_statements=sql_list,
            model_id=model_id,
            erp_config_id=erp_config_id if auto_explain else None
        )
