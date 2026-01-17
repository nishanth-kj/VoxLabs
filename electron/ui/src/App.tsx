import { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { VoiceCloningView } from './views/VoiceCloningView';
import { TextToSpeechView } from './views/TextToSpeechView';
import { Settings, WifiOff } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('voice-cloning');
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('api_url') || 'http://localhost:8000');
  const [isConnected, setIsConnected] = useState(false);

  // URL Input State for Settings View
  const [tempUrl, setTempUrl] = useState(apiUrl);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/status`);
        if (res.ok) setIsConnected(true);
        else setIsConnected(false);
      } catch (e) {
        setIsConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const handleSaveSettings = () => {
    let url = tempUrl.replace(/\/$/, "");
    if (!url.startsWith('http')) {
      alert("Invalid URL");
      return;
    }
    setApiUrl(url);
    localStorage.setItem('api_url', url);
    alert("Settings Saved");
  };

  const handleResetSettings = () => {
    const defaultUrl = 'http://localhost:8000';
    setApiUrl(defaultUrl);
    setTempUrl(defaultUrl);
    localStorage.removeItem('api_url');
  };

  return (
    <div className="flex h-screen bg-background text-primary font-sans overflow-hidden">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isConnected={isConnected}
      />

      <main className="flex-1 overflow-y-auto p-8 relative">
        {!isConnected && (
          <div className="absolute top-0 left-0 right-0 bg-danger text-white text-xs py-1 px-4 text-center flex items-center justify-center gap-2">
            <WifiOff className="w-3 h-3" />
            Disconnected from Engine. Is the backend running?
          </div>
        )}

        {activeTab === 'voice-cloning' && (
          <VoiceCloningView apiUrl={apiUrl} />
        )}

        {activeTab === 'tts' && (
          <TextToSpeechView apiUrl={apiUrl} />
        )}

        {activeTab === 'settings' && (
          <div className="max-w-2xl mx-auto pt-10">
            <header className="mb-8">
              <h1 className="text-3xl font-bold mb-2">Settings</h1>
              <p className="text-secondary">Configure application connection and preferences.</p>
            </header>

            <div className="bg-card border border-border rounded-xl p-8 max-w-lg">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-secondary">Engine API URL</label>
                  <div className="flex gap-2">
                    <input
                      className="flex-1 bg-black/20 border border-border rounded-lg px-4 py-3 text-primary focus:outline-none focus:ring-2 focus:ring-accent"
                      value={tempUrl}
                      onChange={(e) => setTempUrl(e.target.value)}
                    />
                    <button
                      onClick={async () => {
                        try {
                          const res = await fetch(`${tempUrl.replace(/\/$/, "")}/api/status`);
                          if (res.ok) alert("Connected Successfully!");
                          else alert("Connection Failed");
                        } catch (e) {
                          alert("Connection Failed");
                        }
                      }}
                      className="bg-secondary/10 hover:bg-secondary/20 text-secondary px-4 rounded-lg font-medium transition-colors"
                    >
                      Test
                    </button>
                  </div>
                  <p className="text-xs text-secondary">Default: http://localhost:8000</p>
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    onClick={handleResetSettings}
                    className="px-4 py-2 text-sm font-medium text-secondary hover:text-primary transition-colors"
                  >
                    Reset Default
                  </button>
                  <button
                    onClick={handleSaveSettings}
                    className="bg-accent hover:bg-accent-hover text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
                  >
                    <Settings className="w-4 h-4" />
                    Save Changes
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App;
