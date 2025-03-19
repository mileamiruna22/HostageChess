// src/App.js
import React, { useState, useEffect } from 'react';
import { Chess } from 'chess.js';
import './App.css';

function App() {
  // Starea jocului
  const [game, setGame] = useState(new Chess());
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [hostages, setHostages] = useState({
    w: [], // Piesele negre capturate de jucătorul alb
    b: [] // Piesele albe capturate de jucătorul negru
  });
  const [currentPlayer, setCurrentPlayer] = useState('w');
  const [mode, setMode] = useState('normal'); // 'normal' sau 'drop'
  const [selectedHostage, setSelectedHostage] = useState(null);
  const [gameOver, setGameOver] = useState(false);
  const [status, setStatus] = useState('');

  // Inițializarea jocului
  useEffect(() => {
    resetGame();
  }, []);

  // Funcția pentru resetarea jocului
  const resetGame = () => {
    const newGame = new Chess();
    setGame(newGame);
    setSelectedSquare(null);
    setHostages({ w: [], b: [] });
    setCurrentPlayer('w');
    setMode('normal');
    setSelectedHostage(null);
    setGameOver(false);
    setStatus('Jucătorul alb începe.');
  };

  // Funcție pentru mutarea pieselor
  const handleSquareClick = (square) => {
    if (gameOver) return;

    if (mode === 'normal') {
      // Logica pentru mutarea normală
      if (selectedSquare === null) {
        // Selectează piesa pentru mutare
        const piece = game.get(square);
        if (piece && piece.color === currentPlayer) {
          setSelectedSquare(square);
        }
      } else {
        // Încearcă să mute piesa
        try {
          // Verifică dacă mutarea este validă
          const move = game.move({
            from: selectedSquare,
            to: square,
            promotion: 'q' // Promovează la regină în mod implicit
          });

          if (move) {
            // Dacă mutarea include o captură, adaugă piesa la hostages
            if (move.captured) {
              const capturedPiece = move.captured;
              const capturedColor = move.color === 'w' ? 'b' : 'w';
              setHostages(prevHostages => {
                const newHostages = { ...prevHostages };
                newHostages[move.color].push({
                  type: capturedPiece,
                  color: capturedColor
                });
                return newHostages;
              });
            }

            // Actualizează starea jocului
            setSelectedSquare(null);
            setCurrentPlayer(game.turn());
            checkGameStatus();
          } else {
            // Dacă mutarea nu este validă, resetează selecția
            setSelectedSquare(null);
          }
        } catch (e) {
          // Dacă se produce o eroare, resetează selecția
          setSelectedSquare(null);
        }
      }
    } else if (mode === 'drop') {
      // Logica pentru plasarea unei piese ostatic
      if (selectedHostage !== null) {
        // Verifică dacă pătratul este gol
        const pieceAtSquare = game.get(square);
        if (!pieceAtSquare) {
          // Modifică poziția FEN pentru a adăuga piesa
          const fen = game.fen();
          const parts = fen.split(' ');
          const board = parts[0];
          
          // Adaugă piesa la poziția corectă (implementare simplificată)
          // Acest lucru necesită o abordare mai complexă pentru a modifica corect FEN
          // Aici ar trebui să manipulați șirul FEN pentru a adăuga piesa
          
          // Actualizează starea jocului
          // Acest cod este doar un exemplu și trebuie adaptat pentru a funcționa cu chess.js
          // și pentru a respecta regulile specifice Hostage Chess
          
          // Elimină piesa din lista de ostatici
          const newHostages = { ...hostages };
          newHostages[currentPlayer] = newHostages[currentPlayer].filter((_, index) => index !== selectedHostage);
          setHostages(newHostages);
          
          // Revine la modul normal
          setMode('normal');
          setSelectedHostage(null);
          
          // Schimbă jucătorul
          setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
          checkGameStatus();
        }
      }
    }
  };

  // Funcție pentru selectarea unei piese ostatic pentru plasare
  const handleHostageSelect = (index) => {
    if (gameOver) return;
    
    setSelectedHostage(index);
    setMode('drop');
  };

  // Verifică starea jocului
  const checkGameStatus = () => {
    if (game.isCheckmate()) {
      setGameOver(true);
      setStatus(`Șah mat! ${currentPlayer === 'w' ? 'Negrul' : 'Albul'} câștigă!`);
    } else if (game.isDraw()) {
      setGameOver(true);
      setStatus('Remiză!');
    } else if (game.isCheck()) {
      setStatus(`Șah! ${currentPlayer === 'w' ? 'Albul' : 'Negrul'} este în șah.`);
    } else {
      setStatus(`Mută ${currentPlayer === 'w' ? 'albul' : 'negrul'}.`);
    }
  };

  // Funcție de randare a tablei de șah
  const renderBoard = () => {
    const squares = [];
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];

    for (let r = 0; r < 8; r++) {
      for (let f = 0; f < 8; f++) {
        const square = files[f] + ranks[r];
        const piece = game.get(square);
        const isSelected = selectedSquare === square;
        const isLight = (r + f) % 2 === 0;

        squares.push(
          <div
            key={square}
            className={`square ${isLight ? 'light' : 'dark'} ${isSelected ? 'selected' : ''}`}
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
    }

    return <div className="board">{squares}</div>;
  };

  // Funcție pentru randarea pieselor
  const renderPiece = (type, color) => {
    const pieceSymbols = {
      'p': color === 'w' ? '♙' : '♟',
      'n': color === 'w' ? '♘' : '♞',
      'b': color === 'w' ? '♗' : '♝',
      'r': color === 'w' ? '♖' : '♜',
      'q': color === 'w' ? '♕' : '♛',
      'k': color === 'w' ? '♔' : '♚'
    };
    return pieceSymbols[type];
  };

  // Funcție pentru randarea ostaticilor
  const renderHostages = (color) => {
    return (
      <div className={`hostages hostages-${color}`}>
        <h3>{color === 'w' ? 'Ostatici Albi' : 'Ostatici Negri'}</h3>
        <div className="hostages-list">
          {hostages[color].map((piece, index) => (
            <div
              key={index}
              className={`hostage ${currentPlayer === color && 'active'}`}
              onClick={() => currentPlayer === color && handleHostageSelect(index)}
            >
              {renderPiece(piece.type, piece.color)}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="App">
      <h1>Hostage Chess</h1>
      <div className="game-container">
        {renderHostages('b')}
        <div className="board-container">
          {renderBoard()}
          <div className="status">{status}</div>
          <button className="reset-button" onClick={resetGame}>Resetează Jocul</button>
        </div>
        {renderHostages('w')}
      </div>
    </div>
  );
}

export default App;