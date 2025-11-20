"""
EXPLAIN性能分析模块
分析PostgreSQL执行计划并提取性能指标
"""
import json
from typing import Dict, Any, Optional, List
from app.core.database import ERPDatabaseConnection


class ExplainAnalyzer:
    """EXPLAIN分析器"""
    
    def __init__(self, erp_connection: ERPDatabaseConnection):
        """
        初始化EXPLAIN分析器
        
        Args:
            erp_connection: ERP数据库连接
        """
        self.connection = erp_connection
    
    def execute_explain(self, sql: str) -> Optional[str]:
        """
        执行EXPLAIN分析
        
        Args:
            sql: SQL语句
            
        Returns:
            EXPLAIN结果（JSON格式字符串）
        """
        try:
            # 检查SQL类型，只对SELECT语句执行EXPLAIN
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith('SELECT'):
                return None
            
            # 构建EXPLAIN命令
            explain_sql = f"EXPLAIN (ANALYZE false, VERBOSE, BUFFERS, FORMAT JSON) {sql}"
            
            with self.connection.get_cursor() as cursor:
                cursor.execute(explain_sql)
                result = cursor.fetchone()
                
                if result and result[0]:
                    return json.dumps(result[0], ensure_ascii=False, indent=2)
                
                return None
                
        except Exception as e:
            # 如果EXPLAIN失败，返回错误信息
            return f"EXPLAIN执行失败: {str(e)}"
    
    def parse_explain_result(self, explain_json: str) -> Dict[str, Any]:
        """
        解析EXPLAIN结果并提取性能指标
        
        Args:
            explain_json: EXPLAIN结果（JSON格式）
            
        Returns:
            性能指标字典
        """
        try:
            if explain_json.startswith("EXPLAIN执行失败"):
                return {
                    'error': explain_json,
                    'metrics': {}
                }
            
            explain_data = json.loads(explain_json)
            
            if not explain_data or len(explain_data) == 0:
                return {'error': 'Empty EXPLAIN result', 'metrics': {}}
            
            # 获取执行计划根节点
            plan = explain_data[0].get('Plan', {})
            
            # 提取关键性能指标
            metrics = {
                'total_cost': plan.get('Total Cost', 0),
                'startup_cost': plan.get('Startup Cost', 0),
                'plan_rows': plan.get('Plan Rows', 0),
                'plan_width': plan.get('Plan Width', 0),
                'node_type': plan.get('Node Type', ''),
                'scan_types': self._extract_scan_types(plan),
                'join_types': self._extract_join_types(plan),
                'has_index_scan': self._has_node_type(plan, 'Index Scan'),
                'has_seq_scan': self._has_node_type(plan, 'Seq Scan'),
                'has_nested_loop': self._has_node_type(plan, 'Nested Loop'),
                'max_depth': self._calculate_plan_depth(plan),
            }
            
            # 生成性能评估
            assessment = self._assess_performance(metrics)
            
            return {
                'metrics': metrics,
                'assessment': assessment,
                'full_plan': explain_data
            }
            
        except Exception as e:
            return {
                'error': f'解析EXPLAIN结果失败: {str(e)}',
                'metrics': {}
            }
    
    def _extract_scan_types(self, plan: Dict) -> List[str]:
        """提取扫描类型"""
        scan_types = set()
        
        def traverse(node):
            node_type = node.get('Node Type', '')
            if 'Scan' in node_type:
                scan_types.add(node_type)
            
            # 递归处理子节点
            for child in node.get('Plans', []):
                traverse(child)
        
        traverse(plan)
        return list(scan_types)
    
    def _extract_join_types(self, plan: Dict) -> List[str]:
        """提取JOIN类型"""
        join_types = set()
        
        def traverse(node):
            node_type = node.get('Node Type', '')
            if 'Join' in node_type or 'Loop' in node_type:
                join_types.add(node_type)
            
            # 递归处理子节点
            for child in node.get('Plans', []):
                traverse(child)
        
        traverse(plan)
        return list(join_types)
    
    def _has_node_type(self, plan: Dict, target_type: str) -> bool:
        """检查是否包含特定节点类型"""
        def traverse(node):
            if target_type in node.get('Node Type', ''):
                return True
            
            # 递归检查子节点
            for child in node.get('Plans', []):
                if traverse(child):
                    return True
            
            return False
        
        return traverse(plan)
    
    def _calculate_plan_depth(self, plan: Dict) -> int:
        """计算执行计划深度"""
        def traverse(node):
            children = node.get('Plans', [])
            if not children:
                return 1
            
            return 1 + max(traverse(child) for child in children)
        
        return traverse(plan)
    
    def _assess_performance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        性能评估
        
        Args:
            metrics: 性能指标
            
        Returns:
            评估结果
        """
        issues = []
        suggestions = []
        severity = 'low'
        
        # 检查全表扫描
        if metrics.get('has_seq_scan') and metrics.get('plan_rows', 0) > 1000:
            issues.append('存在大表全表扫描（Seq Scan）')
            suggestions.append('建议为常用查询字段创建索引')
            severity = 'high'
        
        # 检查嵌套循环
        if metrics.get('has_nested_loop') and metrics.get('plan_rows', 0) > 10000:
            issues.append('大数据量使用嵌套循环（Nested Loop）可能影响性能')
            suggestions.append('考虑使用Hash Join或Merge Join')
            if severity == 'low':
                severity = 'medium'
        
        # 检查成本
        total_cost = metrics.get('total_cost', 0)
        if total_cost > 10000:
            issues.append(f'查询成本较高（{total_cost:.2f}）')
            suggestions.append('优化查询条件，减少扫描行数')
            if severity == 'low':
                severity = 'medium'
        
        # 检查计划深度
        max_depth = metrics.get('max_depth', 0)
        if max_depth > 5:
            issues.append(f'执行计划层次较深（{max_depth}层）')
            suggestions.append('考虑简化查询或拆分子查询')
            if severity == 'low':
                severity = 'medium'
        
        return {
            'severity': severity,
            'issues': issues,
            'suggestions': suggestions,
            'score': self._calculate_score(metrics, issues)
        }
    
    def _calculate_score(self, metrics: Dict[str, Any], issues: List[str]) -> int:
        """
        计算性能评分（0-100）
        
        Args:
            metrics: 性能指标
            issues: 问题列表
            
        Returns:
            评分
        """
        score = 100
        
        # 根据问题数量扣分
        score -= len(issues) * 15
        
        # 根据成本扣分
        total_cost = metrics.get('total_cost', 0)
        if total_cost > 1000:
            score -= min(30, int(total_cost / 1000) * 5)
        
        # 根据扫描类型调整
        if metrics.get('has_index_scan'):
            score += 10
        
        if metrics.get('has_seq_scan') and metrics.get('plan_rows', 0) > 1000:
            score -= 20
        
        return max(0, min(100, score))
