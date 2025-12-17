
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const InvestmentReportPage = () => {
  const [ticker, setTicker] = useState('920185.BJ');
  const [userInfo, setUserInfo] = useState('');
  const [reportPeriod, setReportPeriod] = useState('3'); // Add state for reportPeriod
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load default values from config on initial render
  useEffect(() => {
    axios.get('/api/config')
      .then(response => {
        // Note: We are removing userInfo from the main config page, so this might be empty.
        // It's better to keep the default as empty string.
        if (response.data.ifind?.reportPeriod) {
          setReportPeriod(response.data.ifind.reportPeriod);
        }
      })
      .catch(error => {
        console.error("Could not pre-load config:", error);
      });
  }, []);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ticker) {
      setError('股票代码不能为空。');
      return;
    }
    
    setIsLoading(true);
    setError('');

    try {
      // Include reportPeriod in the POST request
      const response = await axios.post('/api/run/investment_report', { ticker, userInfo, reportPeriod });
      if (response.data.report_url) {
        // Open the report in a new tab
        window.open(response.data.report_url, '_blank');
      } else {
        setError('未能获取报告URL，请检查后端服务。');
      }
    } catch (err: any) {
      console.error("Error generating investment report:", err);
      const errorMessage = err.response?.data?.detail || err.message || '生成报告时发生未知错误。';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h1>投资研究报告</h1>
      <p>输入一个北交所的股票代码，并可选择性地提供补充信息。系统将执行完整的数据获取、分析、绘图和报告生成流程，并最终产出一份专业的HTML投研报告。</p>
      
      <div className="card bg-light mb-4">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row">
              <div className="col-md-9 mb-3">
                <label htmlFor="ticker" className="form-label">股票代码</label>
                <input
                  type="text"
                  id="ticker"
                  className="form-control"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  placeholder="例如: 920185.BJ"
                  disabled={isLoading}
                  required
                />
              </div>
              <div className="col-md-3 mb-3">
                <label htmlFor="reportPeriod" className="form-label">财报报告期</label>
                <input
                  type="text"
                  id="reportPeriod"
                  className="form-control"
                  value={reportPeriod}
                  onChange={(e) => setReportPeriod(e.target.value)}
                  disabled={isLoading}
                />
                 <div className="form-text">例如: "8" (最新), "3" (中报)</div>
              </div>
            </div>

            <div className="mb-3">
              <label htmlFor="userInfo" className="form-label">补充信息 (可选)</label>
              <textarea
                id="userInfo"
                className="form-control"
                rows={8}
                value={userInfo}
                onChange={(e) => setUserInfo(e.target.value)}
                placeholder="输入任何您想让AI在分析时额外参考的背景信息、新闻、或个人见解。"
                disabled={isLoading}
              ></textarea>
            </div>

            <button type="submit" className="btn btn-primary btn-lg" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  <span className="ms-2">正在生成报告...</span>
                </>
              ) : (
                '生成研究报告'
              )}
            </button>
          </form>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger mt-4">
          <strong>错误:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default InvestmentReportPage;
