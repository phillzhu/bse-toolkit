
'use client';

import Link from 'next/link';
import React from 'react';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  // Temporarily removed usePathname to fix server-side rendering error
  // const pathname = usePathname();

  return (
    <>
      <header>
        <nav className="navbar navbar-expand-lg navbar-light bg-light border-bottom">
          <div className="container">
            <Link href="/" className="navbar-brand">
              BSE-Toolkit v1.2
            </Link>
            <button
              className="navbar-toggler"
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#navbarNav"
              aria-controls="navbarNav"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarNav">
              <ul className="navbar-nav ms-auto">
                <li className="nav-item">
                  <Link href="/settings" className="nav-link">
                    设置
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/daily-briefing" className="nav-link">
                    每日公告简报
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="/investment-report" className="nav-link">
                    投资研究报告
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </header>
      <main className="container mt-4">
        {children}
      </main>
    </>
  );
}
