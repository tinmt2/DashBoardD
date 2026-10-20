import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Employees from './pages/Employees';
import Analytics from './pages/Analytics';
import UIConcepts from './pages/UIConcepts';
import DashboardConcepts from './pages/DashboardConcepts';
import NavigationConcepts from './pages/NavigationConcepts';
import KPIConcepts from './pages/KPIConcepts';
import type { Chain } from './types';

import OverviewDashboard from './pages/OverviewDashboard';
import Admin from './pages/Admin';
import { NotificationProvider } from './context/NotificationContext';
import { SyncProvider } from './context/SyncContext';

const ChainPage = ({ chain }: { chain: Chain }) => <Dashboard chain={chain} />;

function App() {
  React.useEffect(() => {
    document.title = "Tổng hợp lỗi";
    
    // Direct Base64 Data URI of custom DashBoardD logo (100% bypasses any browser cache)
    const logoDataUri = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA2NCA2NCIgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSJub25lIj4KICA8ZGVmcz4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZGIxLWJnIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzBhMGUxYSIgLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMTgxNTNiIiAvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxsaW5lYXJHcmFkaWVudCBpZD0iZGIxLWJvcmRlciIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMzOGJkZjgiIHN0b3Atb3BhY2l0eT0iMC44NSIgLz4KICAgICAgPHN0b3Agb2Zmc2V0PSI1MCUiIHN0b3AtY29sb3I9IiM4MThjZjgiIHN0b3Atb3BhY2l0eT0iMC4zIiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNjMDg0ZmMiIHN0b3Atb3BhY2l0eT0iMC44NSIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImRiMS1zdGVtIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMzOGJkZjgiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iNTAlIiBzdG9wLWNvbG9yPSIjM2I4MmY2IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiM2MzY2ZjEiIC8+CiAgICA8L2xpbmVhckdyYWRpZW50PgogICAgPGxpbmVhckdyYWRpZW50IGlkPSJkYjEtbG9vcCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCUiIHN0b3AtY29sb3I9IiMwMGYyZmUiIC8+CiAgICAgIDxzdG9wIG9mZnNldD0iMzUlIiBzdG9wLWNvbG9yPSIjMzhiZGY4IiAvPgogICAgICA8c3RvcCBvZmZzZXQ9IjcwJSIgc3RvcC1jb2xvcj0iIzYzNjZmMSIgLz4KICAgIDxzdG9wIG9mZnNldD0iMTAwJSIgc3RvcC1jb2xvcj0iI2E4NTVmNyIgLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8cmFkaWFsR3JhZGllbnQgaWQ9ImRiMS1wdWxzZSIgY3g9IjUwJSIgY3k9IjUwJSIgcj0iNTAlIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzM0ZDM5OSIgLz4KICAgICAgPHN0b3Agb2Zmc2V0PSIxMDAlIiBzdG9wLWNvbG9yPSIjMDU5NjY5IiAvPgogICAgPC9yYWRpYWxHcmFkaWVudD4KICAgIDxmaWx0ZXIgaWQ9ImRiMS1zaGFkb3ciIHg9Ii0yMCUiIHk9Ii0yMCUiIHdpZHRoPSIxNDAlIiBoZWlnaHQ9IjE0MCUiPgogICAgICA8ZmVEcm9wU2hhZG93IGR4PSIwIiBkeT0iMiIgc3RkRGV2aWF0aW9uPSIyLjUiIGZsb29kLWNvbG9yPSIjMDAwIiBmbG9vZC1vcGFjaXR5PSIwLjYiIC8+CiAgICA8L2ZpbHRlcj4KICA8L2RlZnM+CgogIDwhLS0gSGlnaC1jb250cmFzdCBkYXJrIHNxdWlyY2xlIHRpbGUgKGNyaXNwIG9uIGJvdGggd2hpdGUgYW5kIGRhcmsgYnJvd3NlciB0YWJzKSAtLT4KICA8cmVjdCB4PSIyLjUiIHk9IjIuNSIgd2lkdGg9IjU5IiBoZWlnaHQ9IjU5IiByeD0iMTUiIGZpbGw9InVybCgjZGIxLWJnKSIgc3Ryb2tlPSJ1cmwoI2RiMS1ib3JkZXIpIiBzdHJva2Utd2lkdGg9IjEuOCIgLz4KCiAgPCEtLSBEIE1vbm9ncmFtIFN0cnVjdHVyZSAtLT4KICA8ZyBmaWx0ZXI9InVybCgjZGIxLXNoYWRvdykiPgogICAgPCEtLSBPdXRlciBBcmMgb2YgRCAtLT4KICAgIDxwYXRoIAogICAgICBkPSJNMjYgMTYgSDM2IEM0Ni41IDE2IDUzIDIzIDUzIDMyIEM1MyA0MSA0Ni41IDQ4IDM2IDQ4IEgyNiIgCiAgICAgIHN0cm9rZT0idXJsKCNkYjEtbG9vcCkiIAogICAgICBzdHJva2Utd2lkdGg9IjYuOCIgCiAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgCiAgICAgIHN0cm9rZS1saW5lam9pbj0icm91bmQiCiAgICAvPgogICAgPCEtLSBWZXJ0aWNhbCBTcGluZSBvZiBEIC0tPgogICAgPHBhdGggCiAgICAgIGQ9Ik0yMCAxNiBWNDgiIAogICAgICBzdHJva2U9InVybCgjZGIxLXN0ZW0pIiAKICAgICAgc3Ryb2tlLXdpZHRoPSI2LjgiIAogICAgICBzdHJva2UtbGluZWNhcD0icm91bmQiCiAgICAvPgogICAgPCEtLSBSZWFsdGltZSBQdWxzZSBSYWRhciBDb3JlIC0tPgogICAgPGNpcmNsZSBjeD0iMzYiIGN5PSIzMiIgcj0iMy42IiBmaWxsPSJ1cmwoI2RiMS1wdWxzZSkiIC8+CiAgICA8Y2lyY2xlIGN4PSIzNiIgY3k9IjMyIiByPSI2LjYiIHN0cm9rZT0iIzM0ZDM5OSIgc3Ryb2tlLXdpZHRoPSIxLjIiIHN0cm9rZS1vcGFjaXR5PSIwLjc1IiBzdHJva2UtZGFzaGFycmF5PSIyIDIiIC8+CiAgPC9nPgo8L3N2Zz4=";

    const updateIcon = (rel: string, href: string, type?: string) => {
      let link = document.querySelector(`link[rel='${rel}']`) as HTMLLinkElement;
      if (!link) {
        link = document.createElement('link');
        link.rel = rel;
        document.head.appendChild(link);
      }
      if (type) link.type = type;
      link.href = href;
    };

    updateIcon('icon', logoDataUri, 'image/svg+xml');
    updateIcon('shortcut icon', logoDataUri);
    updateIcon('alternate icon', logoDataUri);
  }, []);

  return (
    <HashRouter>
      <NotificationProvider>
        <SyncProvider>
          <Routes>
            <Route path="/admin" element={<Admin />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<OverviewDashboard />} />
              <Route path="ui-concepts" element={<UIConcepts />} />
              <Route path="dashboard-concepts" element={<DashboardConcepts />} />
              <Route path="nav-concepts" element={<NavigationConcepts />} />
              <Route path="kpi-concepts" element={<KPIConcepts />} />
              <Route path="employees" element={<Employees />} />
              <Route path="fpt-shop" element={<ChainPage chain="FPT Shop" />} />
              <Route path="long-chau" element={<ChainPage chain="Long Châu" />} />
              <Route path="vaccine" element={<ChainPage chain="Vaccine" />} />
              <Route path="analytics" element={<Analytics />} />
            </Route>
          </Routes>
        </SyncProvider>
      </NotificationProvider>
    </HashRouter>
  );
}

export default App;
