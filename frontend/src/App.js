import React, { useState } from 'react';
import Draggable from 'react-draggable';
import './App.css';
import Blob from './component/blob';
import Nabbar from './component/Nabbar';
import backgroundImage from './images/backgroundimage.png';

function App() {
  const [blobConfig, setBlobConfig] = useState(() => {
    const saved = localStorage.getItem('blobConfig');
    return saved ? JSON.parse(saved) : {
      color: '#0084ff',
      size: 350,
      sensitivity: 1.0,
      smoothing: 0.05,
      position: { x: 0, y: 0 }
    };
  });

  const [isEditMode, setIsEditMode] = useState(false);
  const [tempPosition, setTempPosition] = useState(blobConfig.position);
  const nodeRef = React.useRef(null);

  const saveConfig = (newConfig) => {
    const updated = { ...blobConfig, ...newConfig };
    setBlobConfig(updated);
    localStorage.setItem('blobConfig', JSON.stringify(updated));
  };

  const handleDrag = (e, data) => {
    setTempPosition({ x: data.x, y: data.y });
  };

  const handleSavePosition = () => {
    saveConfig({ position: tempPosition });
    setIsEditMode(false);
  };

  const appStyle = {
    backgroundImage: `url(${backgroundImage})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed',
    backgroundRepeat: 'no-repeat',
    minHeight: '100vh',
    width: '100vw',
    overflow: 'hidden'
  };

  const blobContainerStyle = {
    width: `${blobConfig.size}px`,
    height: `${blobConfig.size}px`,
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    zIndex: 1000,
    pointerEvents: isEditMode ? 'auto' : 'none',
    border: isEditMode ? '2px dashed rgba(255,255,255,0.5)' : 'none',
    borderRadius: '50%',
    cursor: isEditMode ? 'move' : 'default'
  };

  return (
    <div className="App" style={appStyle}>
      <Nabbar
        blobConfig={blobConfig}
        updateConfig={saveConfig}
        isEditMode={isEditMode}
        setIsEditMode={setIsEditMode}
        savePosition={handleSavePosition}
      />

      <header className="App-header">
        <Draggable
          nodeRef={nodeRef}
          disabled={!isEditMode}
          defaultPosition={blobConfig.position}
          position={isEditMode ? null : blobConfig.position}
          onStop={handleDrag}
        >
          <div ref={nodeRef} style={blobContainerStyle} className="blob-draggable-container">
            <Blob
              color={blobConfig.color}
              sensitivity={blobConfig.sensitivity}
              smoothing={blobConfig.smoothing}
            />
          </div>
        </Draggable>
      </header>
    </div>
  );
}

export default App;
