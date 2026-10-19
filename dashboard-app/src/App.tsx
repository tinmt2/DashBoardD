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
import { NotificationProvider } from './context/NotificationContext';
import { SyncProvider } from './context/SyncContext';

const ChainPage = ({ chain }: { chain: Chain }) => <Dashboard chain={chain} />;

function App() {
  return (
    <HashRouter>
      <NotificationProvider>
        <SyncProvider>
          <Routes>
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
