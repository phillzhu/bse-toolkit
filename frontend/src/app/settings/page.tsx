'use client';

import { useState, useEffect, ChangeEvent, FormEvent } from 'react';
import axios from 'axios';
import { set } from 'lodash'; // Using a robust library for deep object updates

const SettingsPage = () => {
  const [config, setConfig] = useState<any>(null);
  const [status, setStatus] = useState(''); // e.g., 'loading', 'saving', 'success', 'error'

  useEffect(() => {
    setStatus('loading');
    axios.get('/api/config')
      .then(response => {
        // Ensure nested objects exist to prevent rendering errors
        const fetchedConfig = response.data;
        if (!fetchedConfig.llm.dashscope) fetchedConfig.llm.dashscope = {};
        if (!fetchedConfig.llm.openai) fetchedConfig.llm.openai = {};
        if (!fetchedConfig.ifind) fetchedConfig.ifind = {};
        if (!fetchedConfig.ifindPayload) fetchedConfig.ifindPayload = {};
        if (!fetchedConfig.dailyBriefing) fetchedConfig.dailyBriefing = { stockSource: 'all' };
        if (!fetchedConfig.customStockPool) fetchedConfig.customStockPool = '';
        setConfig(fetchedConfig);
        setStatus('');
      })
      .catch(error => {
        console.error("Error fetching config:", error);
        setStatus('error');
      });
  }, []);

  const handleDeepChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    // Use a functional update to ensure we're working with the latest state
    setConfig(prevConfig => {
      // Deep clone the previous config to avoid direct mutation
      const newConfig = JSON.parse(JSON.stringify(prevConfig));
      // Use a robust setter to handle nested paths
      set(newConfig, name, value);
      return newConfig;
    });
  };
  
  // Special handler for JSON text areas
  const handleJsonChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    try {
      const parsedValue = JSON.parse(value);
      setConfig(prevConfig => {
        const newConfig = JSON.parse(JSON.stringify(prevConfig));
        set(newConfig, name, parsedValue);
        return newConfig;
      });
    } catch (error) {
      console.error("Invalid JSON:", error);
      // Optionally, handle the error in the UI
    }
  };


  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setStatus('saving');
    axios.post('/api/config', config)
      .then(response => {
        setStatus('success');
        setTimeout(() => setStatus(''), 2000);
      })
      .catch(error => {
        console.error("Error saving config:", error);
        setStatus('error');
      });
  };

  if (status === 'loading' || !config) {
    return <div>Loading settings...</div>;
  }
  
  if (status === 'error') {
    return <div className="alert alert-danger">Failed to load or save settings. Check console for details.</div>;
  }

  return (
    <div>
      <h1>系统设置</h1>
      <p>在此页面配置系统的所有参数。修改后请务必保存。</p>
      <form onSubmit={handleSubmit}>
        
        <fieldset className="border p-3 mb-4">
          <legend className="w-auto h5">大语言模型 (LLM)</legend>
          <div className="mb-3">
            <label htmlFor="llm.provider" className="form-label">LLM 提供商</label>
            <select className="form-select" name="llm.provider" value={config.llm.provider} onChange={handleDeepChange}>
              <option value="dashscope">DashScope (通义千问)</option>
              <option value="openai">OpenAI 兼容接口</option>
            </select>
          </div>
          
          <div className="p-3 border-start border-4 border-primary mb-3">
            <h6>DashScope (通义千问)</h6>
            <div className="mb-3">
              <label htmlFor="llm.dashscope.apiKey" className="form-label">API Key</label>
              <input type="password" id="llm.dashscope.apiKey" className="form-control" name="llm.dashscope.apiKey" value={config.llm.dashscope.apiKey} onChange={handleDeepChange} />
            </div>
            <div className="mb-3">
              <label htmlFor="llm.dashscope.deepModel" className="form-label fw-bold">深度分析/报告模型 (深)</label>
              <input type="text" id="llm.dashscope.deepModel" className="form-control" name="llm.dashscope.deepModel" value={config.llm.dashscope.deepModel} onChange={handleDeepChange} />
            </div>
             <div className="mb-3">
              <label htmlFor="llm.dashscope.fastModel" className="form-label fw-bold">公告初筛模型 (快)</label>
              <input type="text" id="llm.dashscope.fastModel" className="form-control" name="llm.dashscope.fastModel" value={config.llm.dashscope.fastModel} onChange={handleDeepChange} />
            </div>
          </div>

          <div className="p-3 border-start border-4 border-secondary">
            <h6>OpenAI 兼容接口</h6>
            <div className="mb-3">
              <label htmlFor="llm.openai.apiKey" className="form-label">API Key</label>
              <input type="password" id="llm.openai.apiKey" className="form-control" name="llm.openai.apiKey" value={config.llm.openai.apiKey} onChange={handleDeepChange} />
            </div>
            <div className="mb-3">
              <label htmlFor="llm.openai.baseUrl" className="form-label">Base URL</label>
              <input type="text" id="llm.openai.baseUrl" className="form-control" name="llm.openai.baseUrl" value={config.llm.openai.baseUrl} onChange={handleDeepChange} />
            </div>
            <div className="mb-3">
              <label htmlFor="llm.openai.deepModel" className="form-label fw-bold">深度分析/报告模型 (深)</label>
              <input type="text" id="llm.openai.deepModel" className="form-control" name="llm.openai.deepModel" value={config.llm.openai.deepModel} onChange={handleDeepChange} />
            </div>
            <div className="mb-3">
              <label htmlFor="llm.openai.fastModel" className="form-label fw-bold">公告初筛模型 (快)</label>
              <input type="text" id="llm.openai.fastModel" className="form-control" name="llm.openai.fastModel" value={config.llm.openai.fastModel} onChange={handleDeepChange} />
            </div>
          </div>
        </fieldset>

        <fieldset className="border p-3 mb-4">
          <legend className="w-auto h5">全局 iFind 配置</legend>
           <div className="mb-3">
              <label htmlFor="ifind.accessToken" className="form-label">Access Token</label>
              <input type="password" id="ifind.accessToken" className="form-control" name="ifind.accessToken" value={config.ifind.accessToken} onChange={handleDeepChange} />
              <div className="form-text">用于所有 iFind 数据查询的全局访问令牌。</div>
            </div>
        </fieldset>

        <fieldset className="border p-3 mb-4">
          <legend className="w-auto h5">自选股池</legend>
           <div className="mb-3">
              <label htmlFor="customStockPool" className="form-label">自选股票代码列表</label>
              <textarea id="customStockPool" className="form-control" name="customStockPool" rows={5} value={config.customStockPool} onChange={handleDeepChange}></textarea>
              <div className="form-text">在此处维护您的自选股列表，用于“每日公告简报”功能。请使用逗号分隔。</div>
            </div>
        </fieldset>

        <fieldset className="border p-3 mb-4">
          <legend className="w-auto h5">北交所全市场代码列表</legend>
          <div className="mb-3">
            <textarea id="ifindPayload.codes" className="form-control" name="ifindPayload.codes" rows={5} value={config.ifindPayload.codes} onChange={handleDeepChange}></textarea>
            <div className="form-text">此列表仅在“每日公告简报”的公告来源选择“北交所全市场”时生效。通常不需要修改。</div>
          </div>
        </fieldset>

        <button type="submit" className="btn btn-primary btn-lg" disabled={status === 'saving'}>
          {status === 'saving' ? '正在保存...' : '保存设置'}
        </button>
        {status === 'success' && <span className="ms-3 text-success">保存成功！</span>}
      </form>
    </div>
  );
};

export default SettingsPage;