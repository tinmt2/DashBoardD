import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { TaskProvider } from './context/TaskContext';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <HashRouter>
      <TaskProvider>
        <App />
      </TaskProvider>
    </HashRouter>
  </React.StrictMode>
);
