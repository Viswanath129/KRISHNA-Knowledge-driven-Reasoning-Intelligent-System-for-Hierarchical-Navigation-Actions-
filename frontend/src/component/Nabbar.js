import React, { useState, useEffect } from 'react';
import './Nabbar.css';

const Nabbar = ({ blobConfig, updateConfig, isEditMode, setIsEditMode, savePosition }) => {
    const [scrolled, setScrolled] = useState(false);
    const [showSettings, setShowSettings] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            if (window.scrollY > 50) {
                setScrolled(true);
            } else {
                setScrolled(false);
            }
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const toggleSettings = () => setShowSettings(!showSettings);

    const handleColorChange = (e) => {
        updateConfig({ color: e.target.value });
    };

    const handleSizeChange = (e) => {
        updateConfig({ size: parseInt(e.target.value) });
    };

    const handleSensitivityChange = (e) => {
        updateConfig({ sensitivity: parseFloat(e.target.value) });
    };

    return (
        <nav className={`navbar-container ${scrolled ? 'scrolled' : ''}`}>
            <div className="navbar-logo">
                KRISHNA
            </div>

            <ul className="navbar-links">
                <li><a href="#home" className="nav-item">HOME</a></li>
                <li><a href="#vision" className="nav-item">VISION</a></li>
                <li className="settings-menu-item">
                    <span className="nav-item dropdown-trigger" onClick={toggleSettings}>
                        SETTINGS {showSettings ? '▲' : '▼'}
                    </span>

                    {showSettings && (
                        <div className="settings-dropdown">
                            <div className="settings-section">
                                <h3>BLOB CONFIG</h3>

                                <div className="control-group">
                                    <label>COLOR</label>
                                    <input
                                        type="color"
                                        value={blobConfig.color}
                                        onChange={handleColorChange}
                                    />
                                </div>

                                <div className="control-group">
                                    <label>SIZE: {blobConfig.size}px</label>
                                    <input
                                        type="range"
                                        min="100"
                                        max="600"
                                        value={blobConfig.size}
                                        onChange={handleSizeChange}
                                    />
                                </div>

                                <div className="control-group">
                                    <label>SENSITIVITY: {blobConfig.sensitivity.toFixed(1)}</label>
                                    <input
                                        type="range"
                                        min="0.1"
                                        max="3.0"
                                        step="0.1"
                                        value={blobConfig.sensitivity}
                                        onChange={handleSensitivityChange}
                                    />
                                </div>

                                <div className="control-group drag-control">
                                    <label>POSITIONING</label>
                                    {!isEditMode ? (
                                        <button
                                            className="settings-btn"
                                            onClick={() => { setIsEditMode(true); setShowSettings(false); }}
                                        >
                                            EDIT POSITION
                                        </button>
                                    ) : (
                                        <button
                                            className="settings-btn save-btn"
                                            onClick={savePosition}
                                        >
                                            SAVE POSITION
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </li>
            </ul>

            <div className="navbar-actions">
                <button className="nav-btn btn-primary">INITIALIZE</button>
            </div>
        </nav>
    );
};

export default Nabbar;
