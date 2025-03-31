import React from 'react';
import './homePage.css';

const HomePage = ({ onGameStart }) => {
  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="game-title">Hostage Chess</h1>
        <div className="chess-decoration">
          <div className="chess-piece knight"></div>
          <div className="chess-piece rook"></div>
          <div className="chess-piece queen"></div>
          <div className="chess-piece king"></div>
          <div className="chess-piece bishop"></div>
          <div className="chess-piece pawn"></div>
        </div>
        <h2 className="welcome-text">Welcome to the ultimate chess experience</h2>
        <div className="game-modes">
          <button 
            className="game-mode-btn" 
            onClick={() => onGameStart('friend')}
          >
            <div className="btn-icon friend-icon"></div>
            <span>Play with a Friend</span>
          </button>
          <button 
            className="game-mode-btn" 
            onClick={() => onGameStart('computer')}
          >
            <div className="btn-icon computer-icon"></div>
            <span>Play against Computer</span>
          </button>
        </div>
        <div className="footer">
          <p>Select your game mode to begin</p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;