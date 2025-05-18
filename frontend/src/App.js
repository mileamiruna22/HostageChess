// src/App.js
import React, { useState, useEffect } from 'react';
import { Chess } from 'chess.js';
import './App.css';
import HomePage from './homePage';



import pionAlb from './icons/pion alb.png';
import pionNegru from './icons/pion negru.png';
import caluAlb from './icons/calu alb.png';
import caluNegru from './icons/calu negru.png';
import nebunuAlb from './icons/nebunu alb.png';
import nebunuNegru from './icons/nebunu negru.png';
import turaAlba from './icons/tura alba.png';
import turaNeagra from './icons/tura neagra.png';
import reginaAlba from './icons/regina alba.png';
import reginaNeagra from './icons/regina neagra.png';
import regeAlb from './icons/rege alb.png';
import regeNegru from './icons/rege negru.png';




function App() {
  // Adăugăm starea pentru a controla dacă jocul a început
  const [gameStarted, setGameStarted] = useState(false);
  const [gameMode, setGameMode] = useState(null);

  // Game state
  const [game, setGame] = useState(new Chess());
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [isLegalMoveSquare, setLegalMoveSquare] = useState(null);
  const [hostages, setHostages] = useState({
    w: [], // Black pieces captured by white
    b: []  // White pieces captured by black
  });
  const [reserves, setReserves] = useState({
    w: [], // White pieces recovered
    b: []  // Black pieces recovered
  });
  const [currentPlayer, setCurrentPlayer] = useState('w');
  const [mode, setMode] = useState('normal'); // 'normal', 'drop', or 'exchange'
  const [selectedPiece, setSelectedPiece] = useState(null);

  const [selectedHostageIndex, setSelectedHostageIndex] = useState(null);
  const [gameOver, setGameOver] = useState(false);
  const [status, setStatus] = useState('');
  const [moveHistory, setMoveHistory] = useState([]);

  // Piece values for exchanges
  const pieceValues = {
    'p': 1,
    'n': 3,
    'b': 3,
    'r': 5,
    'q': 9,
    'k': Infinity
  };

  // Handler pentru începerea jocului
  const handleGameStart = (mode) => {
    setGameMode(mode);
    setGameStarted(true);
    resetGame();
  };

  // Initialize the game
  useEffect(() => {
    resetGame();
  }, []);

  // Reset game function
  const resetGame = () => {
    const newGame = new Chess();
    setGame(newGame);
    setSelectedSquare(null);
    setLegalMoveSquare(null);
    setHostages({ w: [], b: [] });
    setReserves({ w: [], b: [] });
    setCurrentPlayer('w');
    setMode('normal');
    setSelectedPiece(null);
    setSelectedHostageIndex(null);
    setGameOver(false);
    setStatus('White player starts.');
    setMoveHistory([]);
  };

  // Handle square click
  const [legalMoves, setLegalMoves] = useState([]);

  const handleSquareClick = (square) => {
    if (gameOver) return;

    if (mode === 'normal') {
      // Normal move logic
      if (selectedSquare === null) {
        // Select piece to move
        const piece = game.get(square);
        if (piece && piece.color === currentPlayer) {
          setSelectedSquare(square);
                          const moves = game.moves({ square, verbose: true });
                          const destinations = moves.map(move => move.to);
                          setLegalMoves(destinations);
        }
      } else {
        // Try to move the piece
        try {
          // Check if move is valid
          const move = game.move({
            from: selectedSquare,
            to: square,
            promotion: 'q' // Default promotion to queen
          });

          if (move) {
            // If move includes a capture, add piece to hostages
            if (move.captured) {
              const capturedPiece = move.captured;
              const capturedColor = move.color === 'w' ? 'b' : 'w';
              setHostages(prevHostages => {
                const newHostages = {
                  w: [...prevHostages.w],
                  b: [...prevHostages.b]
                };
                const attackerColor = move.color;
                newHostages[attackerColor].push({
                  type: capturedPiece,
                  color: capturedColor
                });
                return newHostages;
              });
              
            }

            // Add move to history
            setMoveHistory(prev => [...prev, {
              from: move.from,
              to: move.to,
              piece: move.piece,
              color: move.color,
              captured: move.captured,
              san: move.san
            }]);

            // Update game state
            setSelectedSquare(null);
            setLegalMoveSquare(null);
            setCurrentPlayer(game.turn());
            checkGameStatus();
          } else {
            // If move is invalid, reset selection
            setSelectedSquare(null);
            setLegalMoveSquare(null);
          }
                                      setLegalMoves([]);
        } catch (e) {
          // If error occurs, reset selection
          setSelectedSquare(null);
        setLegalMoveSquare(null);
        setLegalMoves([]);
        }
      }
    } else if (mode === 'drop') {
      // Logic for dropping a piece from reserves
      if (selectedPiece !== null) {
        // Check if square is empty
        const pieceAtSquare = game.get(square);
        if (!pieceAtSquare) {
          // This is a simplified implementation
          // In a complete implementation, you would need to modify the chess.js library
          // or create custom validation for dropping pieces
          
          console.log(`Dropping ${selectedPiece.type} at ${square}`);
          
          // Remove piece from reserves
          setReserves(prevReserves => {
            const newReserves = { ...prevReserves };
            newReserves[currentPlayer] = newReserves[currentPlayer].filter((_, index) => 
              index !== selectedHostageIndex
            );
            return newReserves;
          });
          
          // Reset mode
          setMode('normal');
          setSelectedPiece(null);
          setSelectedHostageIndex(null);
          
          // Switch player
          setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
          setStatus(`${currentPlayer === 'w' ? 'Black' : 'White'} to move.`);
        }
      }
    }
  };

  // Handle hostage selection for exchange
  const handleHostageSelect = (index) => {
    if (gameOver) return;
    
    const selectedHostage = hostages[currentPlayer][index];
    setSelectedPiece(selectedHostage);
    setSelectedHostageIndex(index);
    setMode('exchange');
    setStatus(`Select a piece to exchange for ${getPieceName(selectedHostage.type)}`);
  };

  // Handle reserve piece selection for drop
  const handleReserveSelect = (index) => {
    if (gameOver) return;
    
    const selectedReserve = reserves[currentPlayer][index];
    setSelectedPiece(selectedReserve);
    setSelectedHostageIndex(index);
    setMode('drop');
    setStatus(`Select a square to drop ${getPieceName(selectedReserve.type)}`);
  };

  // Handle exchange between hostage and own reserve
  const handleExchangeSelect = (index) => {
    if (mode !== 'exchange' || !selectedPiece) return;
    
    const targetHostage = hostages[currentPlayer === 'w' ? 'b' : 'w'][index];
    
    // Check if exchange is valid (selected piece value >= target piece value)
    if (pieceValues[selectedPiece.type] >= pieceValues[targetHostage.type]) {
      // Remove selected piece from hostages
      const newHostages = { ...hostages };
      newHostages[currentPlayer].splice(selectedHostageIndex, 1);
      
      // Remove target piece from opponent's hostages
      const opponentColor = currentPlayer === 'w' ? 'b' : 'w';
      const exchangedPiece = newHostages[opponentColor][index];
      newHostages[opponentColor].splice(index, 1);
      
      // Add exchanged piece to player's reserves
      const newReserves = { ...reserves };
      newReserves[currentPlayer].push({
        type: exchangedPiece.type,
        color: currentPlayer
      });
      
      // Update state
      setHostages(newHostages);
      setReserves(newReserves);
      setMode('normal');
      setSelectedPiece(null);
      setSelectedHostageIndex(null);
      setStatus(`${currentPlayer === 'w' ? 'White' : 'Black'} exchanged a piece. ${currentPlayer === 'w' ? 'Black' : 'White'} to move.`);
      setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
    } else {
      setStatus(`Invalid exchange. Your ${getPieceName(selectedPiece.type)} is not valuable enough to exchange for a ${getPieceName(targetHostage.type)}.`);
      setMode('normal');
      setSelectedPiece(null);
      setSelectedHostageIndex(null);
    }
  };

  // Get piece full name
  const getPieceName = (type) => {
    const pieceNames = {
      'p': 'Pawn',
      'n': 'Knight',
      'b': 'Bishop',
      'r': 'Rook',
      'q': 'Queen',
      'k': 'King'
    };
    return pieceNames[type];
  };

  // Check game status
  const checkGameStatus = () => {
    if (game.isCheckmate()) {
      setGameOver(true);
      setStatus(`Checkmate! ${currentPlayer === 'w' ? 'Black' : 'White'} wins!`);
    } else if (game.isDraw()) {
      setGameOver(true);
      setStatus('Draw!');
    } else if (game.isCheck()) {
      setStatus(`Check! ${currentPlayer === 'w' ? 'Black' : 'White'} is in check.`);
    } else {
      setStatus(`${currentPlayer === 'w' ? 'Black' : 'White'} to move.`);
    }
  };




  // Render chess board
  const renderBoard = () => {
    const squares = [];
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];



    // Add board squares with rank labels
    for (let r = 0; r < 8; r++) {
      // Add rank label
      squares.push(
        <div key={`${ranks[r]}-left`} className="label rank">
          {ranks[r]}
        </div>
      );
      
      // Add squares for this rank
      for (let f = 0; f < 8; f++) {
        const square = files[f] + ranks[r];
        const piece = game.get(square);
        const isSelected = selectedSquare === square;
        const isLight = (r + f) % 2 === 0;
        const isLegalMoveSquare = legalMoves.includes(square);
        squares.push(
          <div
          key={square}
          className={`square ${isLight ? 'light' : 'dark'} ${isSelected ? 'selected' : ''} ${isLegalMoveSquare ? 'selected' : ''}`}
          onClick={() => handleSquareClick(square)}
          >
            {piece && (
              <div className="piece">
                {renderPiece(piece.type, piece.color)}
              </div>
            )}
          </div>
        );
      }
      
      // Add rank label (right side)
      squares.push(
        <div key="corner-bottom" className="label corner"></div>
      );
      
    }
    
    // Add file labels (bottom)
    for (let f = -1; f < 8; f++) {
      squares.push(
        <div key={`bottom-${files[f]}`} className="label file">
          {files[f]}
        </div>
      );
    }


    


    return <div className="board">{squares}</div>;
  };

  // Render piece
  const renderPiece = (type, color) => {
    const pieceImagePaths = {
      'p': color === 'w' ? pionAlb : pionNegru,
      'n': color === 'w' ? caluAlb : caluNegru,
      'b': color === 'w' ? nebunuAlb : nebunuNegru,
      'r': color === 'w' ? turaAlba : turaNeagra,
      'q': color === 'w' ? reginaAlba : reginaNeagra,
      'k': color === 'w' ? regeAlb : regeNegru
    };
    
    return (
      <img
        src={pieceImagePaths[type]}
        alt={`${color}${type}`}
        className="chess-piece"
      />
    );
  };

  // Render hostages
  const renderHostages = (color) => {
    const label = color === 'w' ? 'White Hostages' : 'Black Hostages';
    const opponentColor = color === 'w' ? 'b' : 'w';
    
    return (
      <div className={`hostages hostages-${color}`}>
        <h3>{label}</h3>
        <div className="hostages-list">
          {hostages[color].map((piece, index) => (
            <div
              key={index}
              className={`hostage ${mode === 'exchange' && currentPlayer !== color ? 'exchange-target' : ''}`}
              onClick={() => {
                if (mode === 'exchange' && currentPlayer !== color) {
                  handleExchangeSelect(index);
                } else if (currentPlayer === color) {
                  handleHostageSelect(index);
                }
              }}
              title={`${getPieceName(piece.type)} (Value: ${pieceValues[piece.type]})`}
            >
              {renderPiece(piece.type, piece.color)}
              <span className="piece-value">{pieceValues[piece.type]}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render reserves
  const renderReserves = (color) => {
    const label = color === 'w' ? 'White Reserves' : 'Black Reserves';
    
    return (
      <div className={`reserves reserves-${color}`}>
        <h3>{label}</h3>
        <div className="reserves-list">
          {reserves[color].map((piece, index) => (
            <div
              key={index}
              className={`reserve ${currentPlayer === color ? 'active' : ''}`}
              onClick={() => currentPlayer === color && handleReserveSelect(index)}
              title={getPieceName(piece.type)}
            >
              {renderPiece(piece.type, piece.color)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render move history
  const renderMoveHistory = () => {
    return (
      <div className="move-history">
        <h3>Move History</h3>
        <div className="move-list">
          {moveHistory.map((move, index) => (
            <div key={index} className="move">
              {index % 2 === 0 ? `${Math.floor(index / 2) + 1}. ` : ''}
              {move.san}
              {move.captured ? ` (${getPieceName(move.captured)} captured)` : ''}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render game info
  const renderGameInfo = () => {
    return (
      <div className="game-info">
        <div className="status">{status}</div>
        <div className="buttons">
          <button className="reset-button" onClick={resetGame}>Reset Game</button>
          <button 
            className="mode-button" 
            onClick={() => {
              setMode('normal');
              setSelectedPiece(null);
              setLegalMoveSquare(null);
              setSelectedHostageIndex(null);
              setSelectedSquare(null);
            }}
          >
            Cancel Selection
          </button>
          <button
            className="mode-button"
            onClick={() => {
              setGameStarted(false);
              setGameMode(null);
            }}
            style={{ backgroundColor: '#2196F3' }}
          >
            Back to Home
          </button>
        </div>
        {renderMoveHistory()}
      </div>
    );
  };

  // Renderea condiționată a HomePage sau ChessGame
  return (
    <div className="App">
      {!gameStarted ? (
        // Afisăm HomePage dacă jocul nu a început
        <HomePage onGameStart={handleGameStart} />
      ) : (
        // Afișăm interfața jocului dacă jocul a început
        <>
          <h1>Hostage Chess</h1>
          <div className="game-container">
            <div className="left-panel">
              {renderHostages('b')}
              {renderReserves('w')}
            </div>
            <div className="center-panel">
              <div className="board-container">
                {renderBoard()}
              </div>
              {renderGameInfo()}
            </div>
            <div className="right-panel">
              {renderHostages('w')}
              {renderReserves('b')}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;