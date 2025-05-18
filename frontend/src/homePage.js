import React, { useEffect, useRef } from 'react';
import './homePage.css';

const HomePage = ({ onGameStart }) => {
  const chessPiecesRef = useRef([]);
  
  useEffect(() => {
    // Animation for chess pieces
    if (chessPiecesRef.current.length > 0) {
      chessPiecesRef.current.forEach((piece, index) => {
        setTimeout(() => {
          if (piece) {
            piece.style.opacity = '0';
            piece.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
              piece.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
              piece.style.opacity = '1';
              piece.style.transform = 'translateY(0)';
            }, 100);
          }
        }, index * 150);
      });
    }
  }, []);

  const addPieceRef = (el) => {
    if (el && !chessPiecesRef.current.includes(el)) {
      chessPiecesRef.current.push(el);
    }
  };

  return (
    <div className="home-container">
      <div className="home-content">
        <div className="chess-animation">
          <div className="chess-bg-piece king-bg"></div>
          <div className="chess-bg-piece queen-bg"></div>
        </div>
        
        <h1 className="game-title">Hostage Chess</h1>
        
        <div className="chess-decoration">
          <div className="chess-piece knight" ref={addPieceRef}></div>
          <div className="chess-piece rook" ref={addPieceRef}></div>
          <div className="chess-piece queen" ref={addPieceRef}></div>
          <div className="chess-piece king" ref={addPieceRef}></div>
          <div className="chess-piece bishop" ref={addPieceRef}></div>
          <div className="chess-piece pawn" ref={addPieceRef}></div>
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
          <p>&copy; 2025 Hostage Chess. All rights reserved.</p>
          
        </div>
      </div>
    </div>
  );
};

export default HomePage;