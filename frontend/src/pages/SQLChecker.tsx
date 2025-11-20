import { useState, useEffect, useRef } from 'react';
import { Card, Select, Button, message, Spin, Tag, Divider, Tabs, Input, Progress, Space, Modal, Table, Checkbox } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, DownloadOutlined, SyncOutlined, ReloadOutlined } from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { getModels, getDatabases, checkSQL, batchCheck, checkAllFromERP, getBatchProgress, exportToExcel, exportToPDF, getERPSQLs } from '../services/sqlCheck';
import type { AIModel, ERPDatabase, CheckRecord, BatchProgress } from '../services/sqlCheck';

const { TextArea } = Input;

const SQLChecker = () => {
  const [models, setModels] = useState<AIModel[]>([]);
  const [databases, setDatabases] = useState<ERPDatabase[]>([]);
  const [selectedModel, setSelectedModel] = useState<number>();
  const [selectedDatabase, setSelectedDatabase] = useState<number>();
  const [activeTab, setActiveTab] = useState('single');
  
  // 单个检查
  const [sqlCode, setSqlCode] = useState('SELECT * FROM users WHERE id = 1;');
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleResult, setSingleResult] = useState<CheckRecord | null>(null);
  const [singleCheckTab, setSingleCheckTab] = useState('sql'); // 'sql' 或 'result'
  
  // 批量检查
  const [batchSQLs, setBatchSQLs] = useState('');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchId, setBatchId] = useState<string>('');
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(null);
  const [progressInterval, setProgressInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  
  // 全部检查
  const [allCheckLoading, setAllCheckLoading] = useState(false);
  const [allCheckBatchId, setAllCheckBatchId] = useState<string>('');
  const [allCheckProgress, setAllCheckProgress] = useState<BatchProgress | null>(null);
  
  // SQL选择
  const [sqlListModalVisible, setSqlListModalVisible] = useState(false);
  const [loadingSQLList, setLoadingSQLList] = useState(false);
  const [erpSQLList, setErpSQLList] = useState<{id: number; sql: string}[]>([]);
  const [selectedSQLIds, setSelectedSQLIds] = useState<number[]>([]);
  const [sqlSelectionMode, setSqlSelectionMode] = useState<'single' | 'batch'>('single');
  
  // 按ID加载SQL
  const [loadSQLById, setLoadSQLById] = useState<string>('');
  
  // EXPLAIN结果查看
  const [explainModalVisible, setExplainModalVisible] = useState(false);
  const [currentExplainResult, setCurrentExplainResult] = useState<string>('');

  useEffect(() => {
    loadModels();
    loadDatabases();
  }, []);
  
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval);
      }
    };
  }, [progressInterval]);

  const loadModels = async () => {
    try {
      const response = await getModels();
      console.log('AI模型响应:', response);
      const data = Array.isArray(response.data) ? response.data : [];
      console.log('AI模型数据:', data);
      const activeModels = data.filter((m: AIModel) => m.is_active);
      console.log('启用的AI模型:', activeModels);
      setModels(activeModels);
      if (activeModels.length > 0) {
        setSelectedModel(activeModels[0].id);
      }
      if (activeModels.length === 0) {
        message.info('暂无启用的AI模型，请先在配置管理中添加并启用');
      }
    } catch (error) {
      console.error('加载AI模型失败:', error);
      message.error('加载AI模型失败');
    }
  };

  const loadDatabases = async () => {
    try {
      const response = await getDatabases();
      console.log('ERP数据库响应:', response);
      const data = Array.isArray(response.data) ? response.data : [];
      console.log('ERP数据库数据:', data);
      const activeDatabases = data.filter((d: ERPDatabase) => d.is_active);
      console.log('启用的ERP数据库:', activeDatabases);
      setDatabases(activeDatabases);
      if (activeDatabases.length > 0) {
        setSelectedDatabase(activeDatabases[0].id);
      }
      if (activeDatabases.length === 0) {
        message.info('暂无配置的ERP数据库，请先在配置管理中添加');
      }
    } catch (error) {
      console.error('加载ERP数据库失败:', error);
      message.error('加载ERP数据库失败，请检查后端服务是否正常');
    }
  };

  // 添加ref用于自动滚动
  const streamingResultRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    if (streamingResultRef.current && singleLoading) {
      streamingResultRef.current.scrollTop = streamingResultRef.current.scrollHeight;
    }
  }, [singleResult?.ai_check_result, singleLoading]);

  const handleSingleCheck = async () => {
    if (!selectedModel) {
      message.warning('请选择AI模型');
      return;
    }
    if (!sqlCode.trim()) {
      message.warning('请输入SQL语句');
      return;
    }

    setSingleLoading(true);
    setSingleResult(null);
    setSingleCheckTab('result'); // 自动切换到结果页签
    
    try {
      // 使用流式API
      const response = await fetch('/api/check/single/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sql_statement: sqlCode,
          model_id: selectedModel,
          erp_config_id: selectedDatabase,
        }),
      });

      if (!response.ok) {
        throw new Error('请求失败');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let streamingResult = '';
      let recordId = 0;
      let duration = 0;

      console.log('[Stream] 开始接收流式数据');

      // 初始化结果对象
      const tempResult: any = {
        check_status: 'pending',
        ai_check_result: '',
        check_duration: 0,
      };
      setSingleResult(tempResult);

      while (true) {
        const { done, value } = await reader!.read();
        if (done) {
          console.log('[Stream] 数据流结束');
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data);
              console.log('[Stream] 收到事件:', event.type, event);

              if (event.type === 'status') {
                message.info(event.message, 1.5);
              } else if (event.type === 'start') {
                recordId = event.record_id;
                console.log('[Stream] 开始检查, record_id:', recordId);
              } else if (event.type === 'explain') {
                // 收到EXPLAIN结果
                console.log('[Stream] 收到EXPLAIN结果, 长度:', event.explain_result?.length);
                setSingleResult(prev => ({
                  ...prev!,
                  explain_result: event.explain_result,
                }));
              } else if (event.type === 'content') {
                streamingResult += event.chunk;
                console.log('[Stream] 收到内容块, 当前总长度:', streamingResult.length);
                // 更新显示 - 保留explain_result
                setSingleResult(prev => ({
                  ...tempResult,
                  ...prev,
                  check_status: 'success',
                  ai_check_result: streamingResult,
                }));
              } else if (event.type === 'done') {
                duration = event.duration;
                console.log('[Stream] 检查完成, 耗时:', duration, 'ms');
                setSingleResult(prev => ({
                  ...tempResult,
                  ...prev,
                  id: event.record_id,
                  check_status: 'success',
                  ai_check_result: streamingResult,
                  check_duration: duration,
                }));
                message.success(`检查完成（耗时: ${duration}ms）`);
              } else if (event.type === 'error') {
                console.error('[Stream] 错误:', event.message);
                setSingleResult(prev => ({
                  ...tempResult,
                  ...prev,
                  check_status: 'failed',
                  error_message: event.message,
                }));
                message.error('检查失败');
              }
            } catch (e) {
              console.error('[Stream] JSON解析错误:', data, e);
            }
          }
        }
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '检查失败');
      setSingleResult({
        check_status: 'failed',
        error_message: error.message || '检查失败',
      } as any);
    } finally {
      setSingleLoading(false);
    }
  };
  
  const handleBatchCheck = async () => {
    if (!selectedModel) {
      message.warning('请选择AI模型');
      return;
    }
    if (!batchSQLs.trim()) {
      message.warning('请输入SQL语句');
      return;
    }
    
    // 解析SQL语句（按分号分割）
    const sqls = batchSQLs
      .split(';')
      .map(s => s.trim())
      .filter(s => s.length > 0)
      .map(sql => ({ sql: sql + ';' }));
    
    if (sqls.length === 0) {
      message.warning('没有有效的SQL语句');
      return;
    }

    setBatchLoading(true);
    setBatchProgress(null);
    try {
      const response = await batchCheck({
        sql_statements: sqls,
        model_id: selectedModel,
        erp_config_id: selectedDatabase,
      });
      
      setBatchId(response.data.batch_id);
      message.success(`已提交批量检查,总计 ${sqls.length} 条SQL`);
      
      // 启动进度轮询
      startProgressPolling(response.data.batch_id);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '批量检查失败');
      setBatchLoading(false);
    }
  };
  
  const handleCheckAll = async () => {
    if (!selectedModel) {
      message.warning('请选择AI模型');
      return;
    }
    if (!selectedDatabase) {
      message.warning('请选择ERP数据库');
      return;
    }

    setAllCheckLoading(true);
    setAllCheckProgress(null);
    try {
      const response = await checkAllFromERP({
        erp_config_id: selectedDatabase,
        model_id: selectedModel,
        auto_explain: true,
      });
      
      setAllCheckBatchId(response.data.batch_id);
      message.success(`已启动全部SQL检查,总计 ${response.data.total_count} 条SQL`);
      
      // 启动进度轮询
      startAllCheckProgressPolling(response.data.batch_id);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '全部检查失败');
      setAllCheckLoading(false);
    }
  };
  
  const startProgressPolling = (batchIdToCheck: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await getBatchProgress(batchIdToCheck);
        setBatchProgress(response.data);
        
        if (response.data.status === 'completed') {
          clearInterval(interval);
          setBatchLoading(false);
          message.success('批量检查完成！');
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 2000);
    
    setProgressInterval(interval);
  };
  
  const startAllCheckProgressPolling = (batchIdToCheck: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await getBatchProgress(batchIdToCheck);
        setAllCheckProgress(response.data);
        
        if (response.data.status === 'completed') {
          clearInterval(interval);
          setAllCheckLoading(false);
          message.success('全部SQL检查完成！');
        }
      } catch (error) {
        console.error('获取进度失败:', error);
      }
    }, 2000);
    
    setProgressInterval(interval);
  };
  
  const handleExport = async (batchIdToExport: string, format: 'excel' | 'pdf') => {
    try {
      message.loading(`正在生成${format === 'excel' ? 'Excel' : 'PDF'}文件...`);
      
      const response = format === 'excel' 
        ? await exportToExcel(batchIdToExport)
        : await exportToPDF(batchIdToExport);
      
      // 下载文件
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `sql_check_${batchIdToExport}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      link.click();
      window.URL.revokeObjectURL(url);
      
      message.success('导出成功！');
    } catch (error: any) {
      message.error(error.response?.data?.detail || '导出失败');
    }
  };
  
  const handleLoadSQLList = async (dbId: number, mode: 'single' | 'batch') => {
    setSqlSelectionMode(mode);
    setLoadingSQLList(true);
    setSqlListModalVisible(true);
    setSelectedSQLIds([]);
    
    try {
      const response = await getERPSQLs(dbId);
      setErpSQLList(response.data.sqls || []);
      if (response.data.total === 0) {
        message.warning('该数据库中没有SQL语句');
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载SQL列表失败');
      setSqlListModalVisible(false);
    } finally {
      setLoadingSQLList(false);
    }
  };
  
  const handleLoadSQLById = async (mode: 'single' | 'batch') => {
    if (!selectedDatabase) {
      message.warning('请先选择数据库');
      return;
    }
    
    const ids = loadSQLById.trim();
    if (!ids) {
      message.warning('请输入SQL ID');
      return;
    }
    
    // 验证输入格式（支持单个ID或逗号分隔的多个ID）
    const idPattern = /^\d+(,\s*\d+)*$/;
    if (!idPattern.test(ids)) {
      message.error('ID格式错误，请输入数字ID，多个ID用逗号分隔');
      return;
    }
    
    setLoadingSQLList(true);
    try {
      // 先加载所有SQL
      const response = await getERPSQLs(selectedDatabase);
      const allSQLs = response.data.sqls || [];
      
      // 过滤出指定ID的SQL
      const requestedIds = ids.split(',').map(id => parseInt(id.trim()));
      const filteredSQLs = allSQLs.filter((item: {id: number; sql: string}) => requestedIds.includes(item.id));
      
      if (filteredSQLs.length === 0) {
        message.warning(`未找到ID为 ${ids} 的SQL语句`);
        return;
      }
      
      if (mode === 'single') {
        // 单个检查模式，只取第一个
        setSqlCode(filteredSQLs[0].sql);
        message.success(`已加载ID为 ${filteredSQLs[0].id} 的SQL语句`);
      } else {
        // 批量检查模式
        const sqlText = filteredSQLs.map((s: {id: number; sql: string}) => s.sql).join('\n');
        setBatchSQLs(sqlText);
        message.success(`已加载 ${filteredSQLs.length} 条SQL语句`);
      }
      
      setLoadSQLById(''); // 清空输入框
    } catch (error: any) {
      message.error(error.response?.data?.detail || '加载SQL失败');
    } finally {
      setLoadingSQLList(false);
    }
  };
  
  const handleSelectSQLs = () => {
    if (selectedSQLIds.length === 0) {
      message.warning('请选择至少一个SQL语句');
      return;
    }
    
    const selectedSQLs = erpSQLList.filter(item => selectedSQLIds.includes(item.id));
    
    if (sqlSelectionMode === 'single' && selectedSQLs.length > 0) {
      // 单个检查模式，只取第一个
      setSqlCode(selectedSQLs[0].sql);
      message.success('已加载SQL语句');
    } else if (sqlSelectionMode === 'batch') {
      // 批量检查模式
      const sqlText = selectedSQLs.map(s => s.sql).join('\n');
      setBatchSQLs(sqlText);
      message.success(`已加载 ${selectedSQLs.length} 条SQL语句`);
    }
    
    setSqlListModalVisible(false);
  };
  
  const handleViewExplain = (explainResult: string) => {
    setCurrentExplainResult(explainResult || '未执行EXPLAIN分析');
    setExplainModalVisible(true);
  };

  const renderSingleCheck = () => (
    <>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space>
            <span>选择AI模型：</span>
            <Select
              style={{ width: 250 }}
              value={selectedModel}
              onChange={setSelectedModel}
              options={models.map((m) => ({
                label: m.model_display_name,
                value: m.id,
              }))}
            />
            <span style={{ marginLeft: 16 }}>选择数据库（可选）：</span>
            <Select
              style={{ width: 250 }}
              value={selectedDatabase}
              onChange={setSelectedDatabase}
              allowClear
              placeholder={databases.length === 0 ? '暂无配置的数据库' : '选择数据库'}
              options={databases.map((d) => ({
                label: d.config_name,
                value: d.id,
              }))}
              notFoundContent={databases.length === 0 ? '请先在配置管理中添加ERP数据库' : '没有找到数据库'}
            />
          </Space>
          
          <Space wrap>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                if (!selectedDatabase) {
                  message.warning('请先选择数据库');
                  return;
                }
                handleLoadSQLList(selectedDatabase, 'single');
              }}
            >
              从数据库加载SQL
            </Button>
            <Input
              style={{ width: 200 }}
              placeholder="输入SQL ID(多个用逗号分隔)"
              value={loadSQLById}
              onChange={(e) => setLoadSQLById(e.target.value)}
              onPressEnter={() => handleLoadSQLById('single')}
            />
            <Button
              type="default"
              loading={loadingSQLList}
              onClick={() => handleLoadSQLById('single')}
            >
              按ID加载
            </Button>
            <Button
              type="primary"
              size="large"
              onClick={handleSingleCheck}
              loading={singleLoading}
              icon={<CheckCircleOutlined />}
            >
              开始检查
            </Button>
          </Space>
        </Space>
      </Card>

      <Card>
        <Tabs
          activeKey={singleCheckTab}
          onChange={setSingleCheckTab}
          items={[
            {
              key: 'sql',
              label: 'SQL语句',
              children: (
                <div style={{ border: '1px solid #d9d9d9', borderRadius: 4 }}>
                  <Editor
                    height="500px"
                    defaultLanguage="sql"
                    value={sqlCode}
                    onChange={(value) => setSqlCode(value || '')}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                    }}
                  />
                </div>
              ),
            },
            {
              key: 'result',
              label: '检查结果',
              children: (
                <div>
                  {singleLoading && singleResult && singleResult.ai_check_result && (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <span style={{ fontSize: 16, fontWeight: 500 }}>AI检查结果（实时输出）</span>
                        {(singleResult.explain_result || selectedDatabase) && (
                          <Button 
                            size="small" 
                            type="link"
                            onClick={() => handleViewExplain(singleResult.explain_result || '正在执行EXPLAIN分析...')}
                            disabled={!singleResult.explain_result}
                          >
                            查看EXPLAIN结果
                          </Button>
                        )}
                      </div>
                      <div 
                        ref={streamingResultRef}
                        className="markdown-content"
                        style={{ 
                          whiteSpace: 'normal', 
                          background: '#f5f5f5', 
                          padding: 16, 
                          borderRadius: 4,
                          height: '400px',
                          overflowY: 'auto',
                          fontSize: '14px',
                          lineHeight: '1.6'
                        }}
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {singleResult.ai_check_result}
                        </ReactMarkdown>
                        <span style={{ 
                          display: 'inline-block',
                          width: '2px',
                          height: '16px',
                          backgroundColor: '#1890ff',
                          marginLeft: '2px',
                          animation: 'blink 1s infinite'
                        }} />
                      </div>
                    </div>
                  )}

                  {singleResult && !singleLoading && (
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <Space>
                          <Tag color={singleResult.check_status === 'success' ? 'success' : 'error'} 
                               icon={singleResult.check_status === 'success' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
                            {singleResult.check_status === 'success' ? '检查成功' : '检查失败'}
                          </Tag>
                          {singleResult.check_duration && (
                            <Tag>耗时: {singleResult.check_duration}ms</Tag>
                          )}
                        </Space>
                        {singleResult.explain_result && (
                          <Button 
                            size="small" 
                            type="link"
                            onClick={() => handleViewExplain(singleResult.explain_result || '')}
                          >
                            查看EXPLAIN结果
                          </Button>
                        )}
                      </div>

                      {singleResult.check_status === 'success' && singleResult.ai_check_result && (
                        <>
                          <Divider orientation="left">AI检查结果</Divider>
                          <div 
                            className="markdown-content"
                            style={{ 
                              whiteSpace: 'normal', 
                              background: '#f5f5f5', 
                              padding: 16, 
                              borderRadius: 4,
                              height: '400px',
                              overflowY: 'auto',
                              fontSize: '14px',
                              lineHeight: '1.6'
                            }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {singleResult.ai_check_result}
                            </ReactMarkdown>
                          </div>
                        </>
                      )}

                      {singleResult.error_message && (
                        <>
                          <Divider orientation="left">错误信息</Divider>
                          <div style={{ color: 'red', whiteSpace: 'pre-wrap', background: '#fff2f0', padding: 16, borderRadius: 4 }}>
                            {singleResult.error_message}
                          </div>
                        </>
                      )}

                      {singleResult.performance_metrics && (
                        <>
                          <Divider orientation="left">性能指标</Divider>
                          <pre style={{ background: '#f5f5f5', padding: 16, borderRadius: 4, overflow: 'auto' }}>
                            {JSON.stringify(singleResult.performance_metrics, null, 2)}
                          </pre>
                        </>
                      )}
                    </div>
                  )}

                  {!singleResult && !singleLoading && (
                    <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                      请点击"开始检查"按钮开始 SQL 检查
                    </div>
                  )}
                </div>
              ),
            },
          ]}
        />
      </Card>
      
      {/* 添加闪烁动画 */}
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        
        /* Markdown样式 */
        .markdown-content h1, .markdown-content h2, .markdown-content h3 {
          margin-top: 16px;
          margin-bottom: 12px;
          font-weight: 600;
        }
        .markdown-content h1 { font-size: 20px; }
        .markdown-content h2 { font-size: 18px; }
        .markdown-content h3 { font-size: 16px; }
        .markdown-content p { margin: 8px 0; }
        .markdown-content ul, .markdown-content ol {
          margin: 8px 0;
          padding-left: 24px;
        }
        .markdown-content li { margin: 4px 0; }
        .markdown-content code {
          background: #f0f0f0;
          padding: 2px 6px;
          border-radius: 3px;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 13px;
        }
        .markdown-content pre {
          background: #282c34;
          color: #abb2bf;
          padding: 12px;
          border-radius: 4px;
          overflow-x: auto;
          margin: 12px 0;
        }
        .markdown-content pre code {
          background: none;
          padding: 0;
          color: inherit;
        }
        .markdown-content blockquote {
          border-left: 4px solid #ddd;
          padding-left: 12px;
          margin: 12px 0;
          color: #666;
        }
        .markdown-content table {
          border-collapse: collapse;
          width: 100%;
          margin: 12px 0;
        }
        .markdown-content th, .markdown-content td {
          border: 1px solid #ddd;
          padding: 8px;
          text-align: left;
        }
        .markdown-content th {
          background: #f5f5f5;
          font-weight: 600;
        }
      `}</style>

    </>
  );
  
  const renderBatchCheck = () => (
    <>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space>
            <span>选择AI模型：</span>
            <Select
              style={{ width: 250 }}
              value={selectedModel}
              onChange={setSelectedModel}
              options={models.map((m) => ({
                label: m.model_display_name,
                value: m.id,
              }))}
            />
            <span style={{ marginLeft: 16 }}>选择数据库（可选）：</span>
            <Select
              style={{ width: 250 }}
              value={selectedDatabase}
              onChange={setSelectedDatabase}
              allowClear
              placeholder={databases.length === 0 ? '暂无配置的数据库' : '选择数据库'}
              options={databases.map((d) => ({
                label: d.config_name,
                value: d.id,
              }))}
              notFoundContent={databases.length === 0 ? '请先在配置管理中添加ERP数据库' : '没有找到数据库'}
            />
          </Space>
          
          <Space wrap>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                if (!selectedDatabase) {
                  message.warning('请先选择数据库');
                  return;
                }
                handleLoadSQLList(selectedDatabase, 'batch');
              }}
            >
              从数据库加载SQL
            </Button>
            <Input
              style={{ width: 200 }}
              placeholder="输入SQL ID(多个用逗号分隔)"
              value={loadSQLById}
              onChange={(e) => setLoadSQLById(e.target.value)}
              onPressEnter={() => handleLoadSQLById('batch')}
            />
            <Button
              type="default"
              loading={loadingSQLList}
              onClick={() => handleLoadSQLById('batch')}
            >
              按ID加载
            </Button>
          </Space>

          <div>
            <div style={{ marginBottom: 8 }}>输入SQL语句（每条以分号结尾）：</div>
            <TextArea
              rows={10}
              value={batchSQLs}
              onChange={(e) => setBatchSQLs(e.target.value)}
              placeholder="请输入多条SQL语句，每条以分号(;)结尾&#10;&#10;例如：&#10;SELECT * FROM users;&#10;SELECT * FROM orders WHERE status = 'pending';"
              style={{ fontFamily: 'monospace' }}
            />
          </div>
          
          <Button
            type="primary"
            size="large"
            onClick={handleBatchCheck}
            loading={batchLoading}
            icon={<CheckCircleOutlined />}
          >
            开始批量检查
          </Button>
        </Space>
      </Card>

      {batchProgress && (
        <Card title="检查进度">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Progress 
              percent={batchProgress.progress} 
              status={batchProgress.status === 'completed' ? 'success' : 'active'}
            />
            <Space size="large">
              <Tag color="blue">总计: {batchProgress.total_count}</Tag>
              <Tag color="green">成功: {batchProgress.success_count}</Tag>
              <Tag color="red">失败: {batchProgress.failed_count}</Tag>
              <Tag>已完成: {batchProgress.completed_count}</Tag>
              {batchProgress.remaining_time && (
                <Tag>预计剩余: {batchProgress.remaining_time}秒</Tag>
              )}
            </Space>
            
            {batchProgress.status === 'completed' && (
              <Space>
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={() => handleExport(batchId, 'excel')}
                >
                  导出Excel
                </Button>
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={() => handleExport(batchId, 'pdf')}
                >
                  导出PDF
                </Button>
              </Space>
            )}
          </Space>
        </Card>
      )}
    </>
  );
  
  const renderCheckAll = () => (
    <>
      <Card style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space>
            <span>选择AI模型：</span>
            <Select
              style={{ width: 250 }}
              value={selectedModel}
              onChange={setSelectedModel}
              options={models.map((m) => ({
                label: m.model_display_name,
                value: m.id,
              }))}
            />
            <span style={{ marginLeft: 16 }}>选择ERP数据库：</span>
            <Select
              style={{ width: 250 }}
              value={selectedDatabase}
              onChange={setSelectedDatabase}
              placeholder="请选择数据库"
              options={databases.map((d) => ({
                label: d.config_name,
                value: d.id,
              }))}
            />
          </Space>
          
          <div style={{ padding: 16, background: '#f0f2f5', borderRadius: 4 }}>
            <p><strong>功能说明：</strong></p>
            <ul>
              <li>从选中的ERP数据库中自动获取所有SQL语句</li>
              <li>自动执行EXPLAIN分析，提取性能指标</li>
              <li>批量调用AI模型进行检查</li>
              <li>生成完整的检查报告</li>
            </ul>
          </div>
          
          <Button
            type="primary"
            size="large"
            danger
            onClick={handleCheckAll}
            loading={allCheckLoading}
            icon={<SyncOutlined />}
          >
            开始全部检查
          </Button>
        </Space>
      </Card>

      {allCheckProgress && (
        <Card title="检查进度">
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Progress 
              percent={allCheckProgress.progress} 
              status={allCheckProgress.status === 'completed' ? 'success' : 'active'}
            />
            <Space size="large">
              <Tag color="blue">总计: {allCheckProgress.total_count}</Tag>
              <Tag color="green">成功: {allCheckProgress.success_count}</Tag>
              <Tag color="red">失败: {allCheckProgress.failed_count}</Tag>
              <Tag>已完成: {allCheckProgress.completed_count}</Tag>
              {allCheckProgress.remaining_time && (
                <Tag>预计剩余: {allCheckProgress.remaining_time}秒</Tag>
              )}
            </Space>
            
            {allCheckProgress.status === 'completed' && (
              <Space>
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={() => handleExport(allCheckBatchId, 'excel')}
                >
                  导出Excel
                </Button>
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={() => handleExport(allCheckBatchId, 'pdf')}
                >
                  导出PDF
                </Button>
              </Space>
            )}
          </Space>
        </Card>
      )}
    </>
  );

  return (
    <div>
      <h2>SQL检查</h2>
      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'single',
            label: '单个SQL检查',
            children: renderSingleCheck(),
          },
          {
            key: 'batch',
            label: '批量SQL检查',
            children: renderBatchCheck(),
          },
          {
            key: 'all',
            label: '全部SQL检查',
            children: renderCheckAll(),
          },
        ]}
      />
      
      {/* SQL选择对话框 */}
      <Modal
        title="选择SQL语句"
        open={sqlListModalVisible}
        onOk={handleSelectSQLs}
        onCancel={() => setSqlListModalVisible(false)}
        width={900}
        okText="确定"
        cancelText="取消"
      >
        {loadingSQLList ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin />
            <p style={{ marginTop: 16 }}>正在加载SQL列表...</p>
          </div>
        ) : (
          <Table
            rowSelection={{
              type: sqlSelectionMode === 'single' ? 'radio' : 'checkbox',
              selectedRowKeys: selectedSQLIds,
              onChange: (keys) => setSelectedSQLIds(keys as number[]),
            }}
            columns={[
              {
                title: 'ID',
                dataIndex: 'id',
                key: 'id',
                width: 80,
              },
              {
                title: 'SQL语句',
                dataIndex: 'sql',
                key: 'sql',
                ellipsis: true,
                render: (text: string) => (
                  <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{text}</span>
                ),
              },
            ]}
            dataSource={erpSQLList}
            rowKey="id"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条`,
            }}
          />
        )}
      </Modal>
      
      {/* EXPLAIN结果查看对话框 */}
      <Modal
        title="EXPLAIN分析结果"
        open={explainModalVisible}
        onCancel={() => setExplainModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setExplainModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        <div style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 4,
          maxHeight: '600px',
          overflowY: 'auto',
          fontFamily: 'Monaco, Consolas, monospace',
          fontSize: '13px',
          lineHeight: '1.6',
          whiteSpace: 'pre-wrap'
        }}>
          {currentExplainResult}
        </div>
      </Modal>
    </div>
  );
};

export default SQLChecker;
