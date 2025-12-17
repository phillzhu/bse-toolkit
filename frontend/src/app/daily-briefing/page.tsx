
'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const DailyBriefingPage = () => {
  const getYesterdayDate = () => {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    return yesterday.toISOString().split('T')[0];
  };

  const [startDate, setStartDate] = useState(getYesterdayDate());
  const [endDate, setEndDate] = useState(getYesterdayDate());
  const [stockSource, setStockSource] = useState('all');
  const [isLoading, setIsLoading] = useState(false);
  const [reportUrl, setReportUrl] = useState('');
  const [error, setError] = useState('');
  
  // --- New states for async polling ---
  const [taskId, setTaskId] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Function to poll for status
  const pollStatus = async (currentTaskId: string) => {
    try {
      const response = await axios.get(`/api/status/daily_briefing/${currentTaskId}`);
      const { status, message, report_url, detail } = response.data;

      setStatusMessage(message || `任务状态: ${status}`);

      if (status === 'complete') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setReportUrl(`${report_url}?t=${new Date().getTime()}`);
        setIsLoading(false);
        setTaskId('');
      } else if (status === 'error') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        setError(detail || '后台任务执行失败。');
        setIsLoading(false);
        setTaskId('');
      }
      // If status is 'running', do nothing and let the interval call again
    } catch (err: any) {
      console.error("Error polling status:", err);
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
      setError('轮询任务状态时发生网络错误。');
      setIsLoading(false);
      setTaskId('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setReportUrl('');
    setStatusMessage('正在启动任务...');
    setTaskId('');

    try {
      // Start the background task
      const response = await axios.post('/api/run/daily_briefing', {
        startDate,
        endDate,
        stockSource,
      });

      if (response.status === 202 && response.data.task_id) {
        const newTaskId = response.data.task_id;
        setTaskId(newTaskId);
        setStatusMessage('任务已启动，正在等待后端处理...');
        
        // Start polling
        pollIntervalRef.current = setInterval(() => {
          pollStatus(newTaskId);
        }, 3000); // Poll every 3 seconds

      } else {
        throw new Error('未能获取有效的任务ID。');
      }
    } catch (err: any) {
      console.error("Error starting daily briefing task:", err);
      const errorMessage = err.response?.data?.detail || err.message || '启动任务时发生未知错误。';
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  // Cleanup effect to clear interval when component unmounts
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return (
    <div>
      <h1>每日公告简报</h1>
      <p>选择日期范围和公告来源，系统将获取该时段内的所有相关公告，进行AI分析和总结，并生成一份HTML格式的简报。</p>
      
      <div className="card bg-light mb-4">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row align-items-end">
              <div className="col-md-4">
                <label htmlFor="start-date" className="form-label">开始日期</label>
                <input
                  type="date"
                  id="start-date"
                  className="form-control"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="col-md-4">
                <label htmlFor="end-date" className="form-label">结束日期</label>
                <input
                  type="date"
                  id="end-date"
                  className="form-control"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  disabled={isLoading}
                />
              </div>
              <div className="col-md-3">
                <label htmlFor="stock-source" className="form-label">公告来源</label>
                <select 
                  id="stock-source"
                  className="form-select" 
                  value={stockSource} 
                  onChange={(e) => setStockSource(e.target.value)}
                  disabled={isLoading}
                >
                  <option value="all">北交所全市场</option>
                  <option value="custom">自选股池</option>
                </select>
              </div>
              <div className="col-md-1 d-flex align-items-end">
                <button type="submit" className="btn btn-primary w-100" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                      <span className="visually-hidden">Loading...</span>
                    </>
                  ) : (
                    '生成'
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {isLoading && (
        <div className="alert alert-info mt-4">
          <strong>正在处理中...</strong>
          <p className="mb-0 mt-2">{statusMessage}</p>
          <div className="progress mt-2">
            <div className="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style={{width: '100%'}}></div>
          </div>
        </div>
      )}

      {error && (
        <div className="alert alert-danger mt-4">
          <strong>错误:</strong> {error}
        </div>
      )}

      {reportUrl && (
        <div className="mt-4">
          <h2>简报结果</h2>
          <div className="ratio ratio-1x1" style={{ height: '100vh' }}>
             <iframe src={reportUrl} title="每日公告简报" />
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyBriefingPage;
