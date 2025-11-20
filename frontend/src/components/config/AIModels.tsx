import { useState, useEffect } from 'react';
import { Table, Button, message, Space, Switch, Modal, Form, Input, InputNumber, Select, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getModels, createModel, updateModel, deleteModel, getProviders } from '../../services/sqlCheck';
import type { AIModel, AIProvider } from '../../services/sqlCheck';

const { TextArea } = Input;

const AIModels = () => {
  const [models, setModels] = useState<AIModel[]>([]);
  const [providers, setProviders] = useState<AIProvider[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingModel, setEditingModel] = useState<AIModel | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadModels();
    loadProviders();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const response = await getModels();
      const data = Array.isArray(response.data) ? response.data : [];
      setModels(data);
    } catch (error) {
      console.error('加载AI模型失败:', error);
      message.error('加载AI模型失败');
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await getProviders();
      const data = Array.isArray(response.data) ? response.data : [];
      setProviders(data);
    } catch (error) {
      console.error('加载AI厂家失败:', error);
    }
  };

  const handleAdd = () => {
    setEditingModel(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: AIModel) => {
    setEditingModel(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteModel(id);
      message.success('删除成功');
      loadModels();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingModel) {
        await updateModel(editingModel.id!, values);
        message.success('更新成功');
      } else {
        await createModel(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadModels();
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
      title: '模型名称',
      dataIndex: 'model_display_name',
      key: 'model_display_name',
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 100,
    },
    {
      title: '最大Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 120,
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
      render: (_: any, record: AIModel) => (
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
          添加AI模型
        </Button>
        <Button icon={<ReloadOutlined />} onClick={loadModels}>
          刷新
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={models}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingModel ? '编辑AI模型' : '添加AI模型'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={800}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="provider_id"
            label="AI厂家"
            rules={[{ required: true, message: '请选择AI厂家' }]}
          >
            <Select
              placeholder="选择AI厂家"
              options={providers.map(p => ({
                label: p.provider_display_name,
                value: p.id,
              }))}
            />
          </Form.Item>
          <Form.Item
            name="model_name"
            label="模型标识"
            rules={[{ required: true, message: '请输入模型标识' }]}
          >
            <Input placeholder="如: gpt-4, claude-3" />
          </Form.Item>
          <Form.Item
            name="model_display_name"
            label="显示名称"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="如: GPT-4" />
          </Form.Item>
          <Form.Item
            name="system_prompt"
            label="系统提示词"
            tooltip="系统提示词定义AI的角色和行为方式"
          >
            <TextArea 
              rows={6} 
              placeholder="你是一位资深的PostgreSQL数据库专家和SQL优化顾问..."
              showCount
              maxLength={5000}
            />
          </Form.Item>
          <Form.Item
            name="user_prompt_template"
            label="用户提示词模板"
            tooltip="用户提示词模板，可使用{sql}占位符代表SQL语句"
          >
            <TextArea 
              rows={4} 
              placeholder="请检查以下PostgreSQL SQL语句：\n\nSQL语句：{sql}"
              showCount
              maxLength={2000}
            />
          </Form.Item>
          <Form.Item
            name="max_tokens"
            label="最大Token"
            initialValue={4000}
            rules={[{ required: true, message: '请输入最大Token' }]}
          >
            <InputNumber min={1} max={128000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="temperature"
            label="温度"
            initialValue={0.7}
            rules={[{ required: true, message: '请输入温度' }]}
          >
            <InputNumber min={0} max={2} step={0.1} style={{ width: '100%' }} />
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

export default AIModels;
