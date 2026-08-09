import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DocsPage } from './pages/DocsPage';

export default function App() {
  const [activeTab, setActiveTab] = useState<'home' | 'dashboard' | 'architecture' | 'docs'>('home');
  const [isLiveConnected, setIsLiveConnected] = useState(false);

  useEffect(() => {
    // Check if FastAPI backend is running on 8000
    fetch('http://localhost:8000/health')
      .then(res => {
        if (res.ok) setIsLiveConnected(true);
      })
      .catch(() => setIsLiveConnected(false));
  }, []);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#07090e' }}>
      
      {/* Animated Navbar */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isLiveConnected={isLiveConnected} 
      />

      {/* Dynamic View rendering */}
      <main style={{ flex: 1 }}>
        {activeTab === 'home' && (
          <HomePage onGoToDashboard={() => setActiveTab('dashboard')} />
        )}
        {activeTab === 'dashboard' && (
          <DashboardPage />
        )}
        {activeTab === 'architecture' && (
          <ArchitecturePage />
        )}
        {activeTab === 'docs' && (
          <DocsPage />
        )}
      </main>

      {/* Decent Footer */}
      <Footer />

    </div>
  );
}
