import { useState, useEffect } from 'react';
import { Layout, Menu, message } from 'antd';
import { DatabaseOutlined, CheckCircleOutlined, HistoryOutlined, SettingOutlined } from '@ant-design/icons';
import SQLChecker from './pages/SQLChecker';
import History from './pages/History';
import Config from './pages/Config';
import './App.css';

const { Header, Content, Sider } = Layout;

function App() {
  // 从 localStorage 读取上次选中的页面，默认为 'checker'
  const [currentPage, setCurrentPage] = useState(() => {
    return localStorage.getItem('currentPage') || 'checker';
  });

  // 当页面切换时，保存到 localStorage
  useEffect(() => {
    localStorage.setItem('currentPage', currentPage);
  }, [currentPage]);

  const renderPage = () => {
    switch (currentPage) {
      case 'checker':
        return <SQLChecker />;
      case 'history':
        return <History />;
      case 'config':
        return <Config />;
      default:
        return <SQLChecker />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', marginRight: '50px' }}>
          <DatabaseOutlined /> SQL检查工具
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[currentPage]}
            style={{ height: '100%', borderRight: 0 }}
            items={[
              {
                key: 'checker',
                icon: <CheckCircleOutlined />,
                label: 'SQL检查',
                onClick: () => setCurrentPage('checker'),
              },
              {
                key: 'history',
                icon: <HistoryOutlined />,
                label: '历史记录',
                onClick: () => setCurrentPage('history'),
              },
              {
                key: 'config',
                icon: <SettingOutlined />,
                label: '配置管理',
                onClick: () => setCurrentPage('config'),
              },
            ]}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: '#fff',
              borderRadius: '8px',
            }}
          >
            {renderPage()}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

export default App;
