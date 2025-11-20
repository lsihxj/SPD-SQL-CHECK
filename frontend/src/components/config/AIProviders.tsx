import { useState, useEffect } from 'react';
import { Table, Button, message, Space, Switch, Modal, Form, Input, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getProviders, createProvider, updateProvider, deleteProvider } from '../../services/sqlCheck';
import type { AIProvider } from '../../services/sqlCheck';

const AIProviders = () => {
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProvider, setEditingProvider] = useState<AIProvider | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    try {
      console.log('开始加载AI厂家...');
      const response = await getProviders();
      console.log('AI厂家API响应:', response);
      console.log('AI厂家数据:', response.data);
      const data = Array.isArray(response.data) ? response.data : [];
      console.log('处理后的AI厂家数据:', data);
      setProviders(data);
      if (data.length === 0) {
        message.info('暂无AI厂家数据，请添加');
      }
    } catch (error) {
      console.error('加载AI厂家失败:', error);
      message.error('加载AI厂家失败');
      setProviders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingProvider(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: AIProvider) => {
    setEditingProvider(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteProvider(id);
      message.success('删除成功');
      loadProviders();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingProvider) {
        await updateProvider(editingProvider.id!, values);
        message.success('更新成功');
      } else {
        await createProvider(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadProviders();
    } catch (error) {
      message.error('操作失败');
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
      title: '厂家名称',
      dataIndex: 'provider_display_name',
      key: 'provider_display_name',
    },
    {
      title: 'API端点',
      dataIndex: 'api_endpoint',
      key: 'api_endpoint',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active: boolean) => <Switch checked={active} disabled />,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: AIProvider) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除吗？"
            onConfirm={() => handleDelete(record.id!)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加AI厂家
        </Button>
        <Button icon={<ReloadOutlined />} onClick={loadProviders}>
          刷新
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={providers}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingProvider ? '编辑AI厂家' : '添加AI厂家'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="provider_name"
            label="厂家标识"
            rules={[{ required: true, message: '请输入厂家标识' }]}
          >
            <Input placeholder="如: openai, claude" />
          </Form.Item>
          <Form.Item
            name="provider_display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="如: OpenAI" />
          </Form.Item>
          <Form.Item
            name="api_endpoint"
            label="API端点"
            rules={[{ required: true, message: '请输入API端点' }]}
          >
            <Input placeholder="https://api.openai.com/v1" />
          </Form.Item>
          <Form.Item
            name="api_key"
            label="API密钥"
            rules={[{ required: true, message: '请输入API密钥' }]}
          >
            <Input.Password placeholder="输入API密钥" />
          </Form.Item>
          <Form.Item
            name="is_active"
            label="是否启用"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIProviders;
