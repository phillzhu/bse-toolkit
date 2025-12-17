import Link from 'next/link';

export default function Home() {
  return (
    <div className="p-5 mb-4 bg-light rounded-3">
      <div className="container-fluid py-5">
        <h1 className="display-5 fw-bold text-dark">北交所辅助决策系统</h1>
        <p className="fs-4 text-dark">
          欢迎使用 BSE Toolkit v1.2
        </p>
        <p className="fs-5 text-secondary">
          本系统利用大语言模型（LLM）为您提供数据驱动的投资决策支持
        </p>
        <hr className="my-4" />
        <p className="text-dark">请从以下功能开始：</p>
        <div className="d-flex">
          <Link href="/daily-briefing" className="btn btn-primary btn-lg me-2">
            每日公告简报 &raquo;
          </Link>
          <Link href="/investment-report" className="btn btn-secondary btn-lg me-2">
            投资研究报告 &raquo;
          </Link>
          <Link href="/settings" className="btn btn-success btn-lg">
            进入系统设置 &raquo;
          </Link>
        </div>
      </div>
    </div>
  );
}
