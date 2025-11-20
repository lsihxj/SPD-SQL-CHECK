import { useState, useEffect } from 'react';
import { Table, Button, message, Space, Switch, Modal, Form, Input, InputNumber, Popconfirm } from 'antd';
import { PlusOutlined, ReloadOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getDatabases, createDatabase, updateDatabase, deleteDatabase } from '../../services/sqlCheck';
import type { ERPDatabase } from '../../services/sqlCheck';

const ERPDatabases = () => {
  const [databases, setDatabases] = useState<ERPDatabase[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDatabase, setEditingDatabase] = useState<ERPDatabase | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadDatabases();
  }, []);

  const loadDatabases = async () => {
    setLoading(true);
    try {
      const response = await getDatabases();
      const data = Array.isArray(response.data) ? response.data : [];
      setDatabases(data);
    } catch (error) {
      console.error('加载数据库配置失败:', error);
      message.error('加载数据库配置失败');
      setDatabases([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingDatabase(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: ERPDatabase) => {
    setEditingDatabase(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteDatabase(id);
      message.success('删除成功');
      loadDatabases();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingDatabase) {
        await updateDatabase(editingDatabase.id!, values);
        message.success('更新成功');
      } else {
        await createDatabase(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadDatabases();
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
      title: '配置名称',
      dataIndex: 'config_name',
      key: 'config_name',
    },
    {
      title: '主机',
      dataIndex: 'host',
      key: 'host',
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 100,
    },
    {
      title: '数据库名',
      dataIndex: 'database_name',
      key: 'database_name',
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
      render: (_: any, record: ERPDatabase) => (
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
          添加数据库
        </Button>
        <Button icon={<ReloadOutlined />} onClick={loadDatabases}>
          刷新
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={databases}
        rowKey="id"
        loading={loading}
      />

      <Modal
        title={editingDatabase ? '编辑数据库' : '添加数据库'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="config_name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="如: ERP生产库、ERP测试库" />
          </Form.Item>
          <Form.Item
            name="host"
            label="主机地址"
            rules={[{ required: true, message: '请输入主机地址' }]}
          >
            <Input placeholder="localhost" />
          </Form.Item>
          <Form.Item
            name="port"
            label="端口"
            initialValue={5432}
            rules={[{ required: true, message: '请输入端口' }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="database_name"
            label="数据库名"
            rules={[{ required: true, message: '请输入数据库名' }]}
          >
            <Input placeholder="erp_db" />
          </Form.Item>
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input placeholder="postgres" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password placeholder="输入密码" />
          </Form.Item>
          <Form.Item
            name="sql_query_for_sqls"
            label="获取SQL语句的查询"
            rules={[{ required: true, message: '请输入获取SQL语句的查询' }]}
            tooltip="该查询应返回ID和SQL语句两列,例如: SELECT id, sql_content FROM sql_statements"
          >
            <Input.TextArea 
              rows={3}
              placeholder="SELECT id, sql_content FROM sql_statements WHERE status = 'active'"
            />
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

export default ERPDatabases;
