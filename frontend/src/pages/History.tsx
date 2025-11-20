import { useState, useEffect } from 'react';
import { Table, Card, Tag, DatePicker, Button, Space, message } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { getCheckRecords } from '../services/sqlCheck';
import type { CheckRecord } from '../services/sqlCheck';

const { RangePicker } = DatePicker;

const History = () => {
  const [records, setRecords] = useState<CheckRecord[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRecords();
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await getCheckRecords();
      // 确保数据是数组
      const data = Array.isArray(response.data) ? response.data : [];
      setRecords(data);
    } catch (error) {
      console.error('加载历史记录失败:', error);
      message.error('加载历史记录失败');
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'SQL语句',
      dataIndex: 'sql_statement',
      key: 'sql_statement',
      ellipsis: true,
      width: 300,
    },
    {
      title: '检查状态',
      dataIndex: 'has_issues',
      key: 'has_issues',
      width: 120,
      render: (hasIssues: boolean, record: CheckRecord) => (
        <Tag
          color={hasIssues ? 'error' : 'success'}
          icon={hasIssues ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
        >
          {hasIssues ? `${record.issue_count}个问题` : '通过'}
        </Tag>
      ),
    },
    {
      title: '性能评分',
      dataIndex: 'performance_score',
      key: 'performance_score',
      width: 120,
      render: (score: number) =>
        score ? (
          <Tag color={score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'}>
            {score}分
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: '检查时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
  ];

  return (
    <div>
      <h2>历史记录</h2>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button icon={<ReloadOutlined />} onClick={loadRecords}>
            刷新
          </Button>
        </Space>
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>
    </div>
  );
};

export default History;
