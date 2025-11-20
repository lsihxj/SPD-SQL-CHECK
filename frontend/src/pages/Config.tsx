import { useState, useEffect } from 'react';
import { Tabs } from 'antd';
import AIProviders from '../components/config/AIProviders';
import AIModels from '../components/config/AIModels';
import ERPDatabases from '../components/config/ERPDatabases';

const Config = () => {
  // 从 localStorage 读取上次选中的标签页，默认为 'providers'
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('configActiveTab') || 'providers';
  });

  // 当标签页切换时，保存到 localStorage
  useEffect(() => {
    localStorage.setItem('configActiveTab', activeTab);
  }, [activeTab]);

  return (
    <div>
      <h2>配置管理</h2>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'providers',
            label: 'AI厂家',
            children: <AIProviders />,
          },
          {
            key: 'models',
            label: 'AI模型',
            children: <AIModels />,
          },
          {
            key: 'databases',
            label: 'ERP数据库',
            children: <ERPDatabases />,
          },
        ]}
      />
    </div>
  );
};

export default Config;
