import React, { useState, useEffect } from 'react';
import { Chess } from 'chess.js';
import './App.css';
import HomePage from './homePage';

function App() {
  // Starea jocului
  const [gameStarted, setGameStarted] = useState(false);
  const [gameMode, setGameMode] = useState(null);
  const [game, setGame] = useState(new Chess());
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [hostages, setHostages] = useState({
    w: [], // Piese negre capturate de alb
    b: []  // Piese albe capturate de negru
  });
  const [reserves, setReserves] = useState({
    w: [], // Piese albe recuperate
    b: []  // Piese negre recuperate
  });
  const [currentPlayer, setCurrentPlayer] = useState('w');
  const [mode, setMode] = useState('normal'); // 'normal', 'drop', sau 'exchange'
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [selectedHostageIndex, setSelectedHostageIndex] = useState(null);
  const [gameOver, setGameOver] = useState(false);
  const [status, setStatus] = useState('');
  const [moveHistory, setMoveHistory] = useState([]);

  // Valorile pieselor pentru schimburi
  const pieceValues = {
    'p': 1,
    'n': 3,
    'b': 3,
    'r': 5,
    'q': 9,
    'k': Infinity
  };

  // Inițializăm jocul
  useEffect(() => {
    resetGame();
  }, []);

  // Handler pentru începerea jocului
  const handleGameStart = (mode) => {
    setGameMode(mode);
    setGameStarted(true);
    resetGame();
  };

  // Resetăm jocul
  const resetGame = () => {
    const newGame = new Chess();
    setGame(newGame);
    setSelectedSquare(null);
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

  // Handler pentru clic pe un pătrat de pe tablă
  const handleSquareClick = (square) => {
    if (gameOver) return;

    if (mode === 'normal') {
      // Dacă avem deja o piesă selectată, încercăm să o mutăm
      if (selectedSquare) {
        try {
          // Formăm obiectul pentru mutare
          const moveObj = {
            from: selectedSquare,
            to: square,
            promotion: 'q' // Automat promovare la regină dacă este nevoie
          };

          // Verificăm și executăm mutarea
          const moveResult = game.move(moveObj);
          
          // Dacă mutarea nu este validă, resetăm selecția
          if (!moveResult) {
            setSelectedSquare(null);
            return;
          }

          // Creăm o nouă instanță a jocului pentru a forța re-renderul
          const newGameState = new Chess(game.fen());
          setGame(newGameState);

          // Verificăm dacă a fost o captură
          const capturedPiece = moveResult.captured;
          
          if (capturedPiece) {
            // A avut loc o captură, întrebăm utilizatorul
            const takeHostage = window.confirm(`Ai capturat un ${getPieceName(capturedPiece)}. Vrei să-l iei ca ostatic?`);
            
            if (takeHostage) {
              // Adăugăm piesa capturată la ostatici
              setHostages(prev => {
                const newHostages = { ...prev };
                newHostages[currentPlayer].push({
                  type: capturedPiece,
                  color: currentPlayer === 'w' ? 'b' : 'w'
                });
                return newHostages;
              });
            }
          }

          // Adăugăm mutarea în istoric
          setMoveHistory(prev => [...prev, {
            from: selectedSquare,
            to: square,
            piece: moveResult.piece,
            color: currentPlayer,
            captured: capturedPiece,
            san: game.history().pop()
          }]);

          // Actualizăm jucătorul curent
          setCurrentPlayer(newGameState.turn());
          
          // Resetăm selecția
          setSelectedSquare(null);
          
          // Verificăm starea jocului (șah, șah mat, etc.)
          checkGameStatus(newGameState);
        } catch (error) {
          console.error('Eroare la mutare:', error);
          setSelectedSquare(null);
        }
      } else {
        // Dacă nu avem o piesă selectată, verificăm dacă putem selecta o piesă de aici
        const piece = game.get(square);
        if (piece && piece.color === currentPlayer) {
          setSelectedSquare(square);
        }
      }
    } else if (mode === 'drop') {
      // Logica pentru plasarea unei piese din rezervă
      if (selectedPiece) {
        const pieceAtSquare = game.get(square);
        
        // Verificăm dacă pătratul este liber
        if (!pieceAtSquare) {
          console.log(`Dropping ${selectedPiece.type} at ${square}`);
          
          // Aici ar trebui implementată logica pentru a plasa o piesă pe tablă
          // Notă: chess.js nu are o metodă nativă pentru a plasa piese,
          // ar trebui să creați un nou obiect board cu piesa adăugată
          
          // Actualizăm starea rezervelor
          setReserves(prevReserves => {
            const newReserves = { ...prevReserves };
            newReserves[currentPlayer] = newReserves[currentPlayer].filter((_, index) =>
              index !== selectedHostageIndex
            );
            return newReserves;
          });
          
          // Resetăm modul și selecția
          setMode('normal');
          setSelectedPiece(null);
          setSelectedHostageIndex(null);
          
          // Schimbăm jucătorul
          setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
          setStatus(`${currentPlayer === 'w' ? 'Black' : 'White'} to move.`);
        }
      }
    }
  };

  // Handler pentru selectarea unui ostatic pentru schimb
  const handleHostageSelect = (index) => {
    if (gameOver) return;

    const selectedHostage = hostages[currentPlayer][index];
    setSelectedPiece(selectedHostage);
    setSelectedHostageIndex(index);
    setMode('exchange');
    setStatus(`Select a piece to exchange for ${getPieceName(selectedHostage.type)}`);
  };

  // Handler pentru selectarea unei piese din rezervă pentru plasare
  const handleReserveSelect = (index) => {
    if (gameOver) return;

    const selectedReserve = reserves[currentPlayer][index];
    setSelectedPiece(selectedReserve);
    setSelectedHostageIndex(index);
    setMode('drop');
    setStatus(`Select a square to drop ${getPieceName(selectedReserve.type)}`);
  };

  // Handler pentru schimbul între ostatic și rezervă a adversarului
  const handleExchangeSelect = (index) => {
    if (mode !== 'exchange' || !selectedPiece) return;

    const targetHostage = hostages[currentPlayer === 'w' ? 'b' : 'w'][index];

    // Verifică dacă schimbul este valid (valoarea piesei selectate >= valoarea piesei țintă)
    if (pieceValues[selectedPiece.type] >= pieceValues[targetHostage.type]) {
      // Eliminăm piesa selectată din ostatici
      const newHostages = { ...hostages };
      newHostages[currentPlayer].splice(selectedHostageIndex, 1);

      // Eliminăm piesa țintă din ostaticii adversarului
      const opponentColor = currentPlayer === 'w' ? 'b' : 'w';
      const exchangedPiece = newHostages[opponentColor][index];
      newHostages[opponentColor].splice(index, 1);

      // Adăugăm piesa schimbată la rezervele jucătorului
      const newReserves = { ...reserves };
      newReserves[currentPlayer].push({
        type: exchangedPiece.type,
        color: currentPlayer
      });

      // Actualizăm starea
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

  // Obține numele complet al piesei
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

  // Verificăm starea jocului
  const checkGameStatus = (currentGameState = game) => {
    if (currentGameState.isCheckmate()) {
      setGameOver(true);
      setStatus(`Checkmate! ${currentGameState.turn() === 'w' ? 'Black' : 'White'} wins!`);
    } else if (currentGameState.isDraw()) {
      setGameOver(true);
      setStatus('Draw!');
    } else if (currentGameState.isCheck()) {
      setStatus(`Check! ${currentGameState.turn() === 'w' ? 'White' : 'Black'} is in check.`);
    } else {
      setStatus(`${currentGameState.turn() === 'w' ? 'White' : 'Black'} to move.`);
    }
  };

  // Renderăm tabla de șah
  const renderBoard = () => {
    const squares = [];
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];

    // Adăugăm etichetele pentru rânduri
    squares.push(
      <div key="corner" className="label corner"></div>
    );

    // Adăugăm etichetele pentru coloane (sus)
    for (let f = 0; f < 8; f++) {
      squares.push(
        <div key={`top-${files[f]}`} className="label file">
          {files[f]}
        </div>
      );
    }

    // Adăugăm pătratele tablei cu etichete pentru rânduri
    for (let r = 0; r < 8; r++) {
      // Adăugăm eticheta rândului
      squares.push(
        <div key={`${ranks[r]}-left`} className="label rank">
          {ranks[r]}
        </div>
      );

      // Adăugăm pătratele pentru acest rând
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

      // Adăugăm eticheta rândului (partea dreaptă)
      squares.push(
        <div key={`${ranks[r]}-right`} className="label rank">
          {ranks[r]}
        </div>
      );
    }

    // Adăugăm etichetele pentru coloane (jos)
    squares.push(
      <div key="corner-bottom" className="label corner"></div>
    );

    for (let f = 0; f < 8; f++) {
      squares.push(
        <div key={`bottom-${files[f]}`} className="label file">
          {files[f]}
        </div>
      );
    }

    return <div className="board">{squares}</div>;
  };

  // Renderăm o piesă
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

  // Renderăm ostaticii
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

  // Renderăm rezervele
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

  // Renderăm informațiile despre joc
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

  // Renderarea condiționată a HomePage sau ChessGame
  return (
    <div className="App">
      {!gameStarted ? (
        // Afișăm HomePage dacă jocul nu a început
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