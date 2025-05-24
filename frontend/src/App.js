// src/App.js
import React, { useState, useEffect } from 'react';
import { Chess } from 'chess.js';
import './App.css';
import HomePage from './homePage';
import aiService from './aiService';

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
  const [gameStarted, setGameStarted] = useState(false);
  const [gameMode, setGameMode] = useState(null);
  const [game, setGame] = useState(new Chess());
  const [selectedSquare, setSelectedSquare] = useState(null);
  const [isLegalMoveSquare, setLegalMoveSquare] = useState(null);
  const [hostages, setHostages] = useState({ w: [], b: [] });
  const [reserves, setReserves] = useState({ w: [], b: [] });
  const [currentPlayer, setCurrentPlayer] = useState('w');
  const [mode, setMode] = useState('normal');
  const [selectedPiece, setSelectedPiece] = useState(null);
  const [selectedHostageIndex, setSelectedHostageIndex] = useState(null);
  const [gameOver, setGameOver] = useState(false);
  const [status, setStatus] = useState('');
  const [moveHistory, setMoveHistory] = useState([]);
  const [legalMoves, setLegalMoves] = useState([]);

  const [vsAI, setVsAI] = useState(false);
  const [gameId, setGameId] = useState(null);
  const [aiDifficulty, setAiDifficulty] = useState('medium');
  const [playerColor, setPlayerColor] = useState('w');
  const [isAITurn, setIsAITurn] = useState(false);

  const pieceValues = { 'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': Infinity };

  const handleGameStart = async (mode) => {
    setGameMode(mode);
    setGameStarted(true);
    resetGame();

    if (mode === 'ai') {
      setVsAI(true);
      setPlayerColor('w'); // Jucătorul uman joacă mereu cu alb
      try {
        const response = await aiService.startNewAIGame('w', aiDifficulty);
        setGameId(response.game_id);
        setGame(new Chess(response.fen));
        setCurrentPlayer('w'); // Albul începe
        setStatus('White to move. You play as White.');
        
        // Nu facem mutare AI la început pentru că albul mută primul
      } catch (error) {
        console.error('Eroare la pornirea jocului AI:', error);
        setStatus('Error starting AI game. Please try again.');
      }
    } else {
      setVsAI(false);
      setGameId(null);
    }
  };

  useEffect(() => {
    resetGame();
  }, []);

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
    setIsAITurn(false);
  };

  // Funcție pentru sincronizarea mutării cu backend-ul
  const syncMoveWithBackend = async (moveUci) => {
    if (!vsAI || !gameId) return null;
    
    try {
      const response = await fetch('http://localhost:5000/make_move', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: gameId,
          move: moveUci
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to sync move with backend');
      }

      return await response.json();
    } catch (error) {
      console.error('Error syncing move:', error);
      return null;
    }
  };

  const handleSquareClick = async (square) => {
    if (gameOver || isAITurn) return;
    
    // În modul AI, doar jucătorul uman (alb) poate face mutări
    if (vsAI && currentPlayer !== playerColor) return;

    if (mode === 'normal') {
      if (selectedSquare === null) {
        const piece = game.get(square);
        if (piece && piece.color === currentPlayer) {
          setSelectedSquare(square);
          const moves = game.moves({ square, verbose: true });
          const destinations = moves.map(move => move.to);
          setLegalMoves(destinations);
        }
      } else {
        try {
          const move = game.move({
            from: selectedSquare,
            to: square,
            promotion: 'q'
          });

          if (move) {
            // Sincronizează mutarea cu backend-ul
            let backendResponse = null;
            if (vsAI && gameId) {
              backendResponse = await syncMoveWithBackend(move.from + move.to + (move.promotion || ''));
            }

            // Actualizează ostaticii dacă există captură
            if (move.captured) {
              const capturedPiece = move.captured;
              const capturedColor = move.color === 'w' ? 'b' : 'w';
              setHostages(prev => {
                const updated = { w: [...prev.w], b: [...prev.b] };
                updated[move.color].push({ type: capturedPiece, color: capturedColor });
                return updated;
              });
            }

            // Folosește datele de la backend dacă sunt disponibile
            if (backendResponse) {
              setHostages(backendResponse.hostages || hostages);
            }

            setMoveHistory(prev => [...prev, {
              from: move.from,
              to: move.to,
              piece: move.piece,
              color: move.color,
              captured: move.captured,
              san: move.san
            }]);

            setSelectedSquare(null);
            setLegalMoveSquare(null);
            setCurrentPlayer(game.turn());
            checkGameStatus();
            setLegalMoves([]);

            // Dacă jucăm contra AI și e rândul AI-ului
            if (vsAI && game.turn() !== playerColor) {
              setIsAITurn(true);
              setStatus('AI is thinking...');
              
              // Delay pentru experiența utilizatorului
              setTimeout(async () => {
                await makeAIMove();
              }, 1000);
            }
          } else {
            setSelectedSquare(null);
            setLegalMoveSquare(null);
          }
        } catch (e) {
          console.error('Move error:', e);
          setSelectedSquare(null);
          setLegalMoveSquare(null);
          setLegalMoves([]);
        }
      }
    } else if (mode === 'drop') {
      const pieceAtSquare = game.get(square);
      if (!pieceAtSquare && selectedPiece !== null) {
        console.log(`Dropping ${selectedPiece.type} at ${square}`);
        setReserves(prev => {
          const updated = { ...prev };
          updated[currentPlayer] = updated[currentPlayer].filter((_, idx) => idx !== selectedHostageIndex);
          return updated;
        });
        setMode('normal');
        setSelectedPiece(null);
        setSelectedHostageIndex(null);
        setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
        setStatus(`${currentPlayer === 'w' ? 'Black' : 'White'} to move.`);
      }
    }
  };

  // Funcție pentru mutarea AI
  const makeAIMove = async () => {
    if (!vsAI || !gameId) return;

    try {
      // Obține mutarea AI
      const aiMoveResponse = await aiService.getAIMove(gameId, aiDifficulty);
      
      if (aiMoveResponse.error) {
        console.error('AI Move Error:', aiMoveResponse.error);
        setStatus('AI encountered an error. Your turn.');
        setIsAITurn(false);
        return;
      }

      // Actualizează jocul cu noua poziție
      const newGame = new Chess(aiMoveResponse.fen);
      setGame(newGame);
      setCurrentPlayer(aiMoveResponse.turn);
      
      // Actualizează ostaticii
      if (aiMoveResponse.hostages) {
        setHostages(aiMoveResponse.hostages);
      }

      // Actualizează rezervele dacă există
      if (aiMoveResponse.reserves) {
        setReserves(aiMoveResponse.reserves);
      }

      // Adaugă mutarea în istoric
      if (aiMoveResponse.move) {
        const moveObj = {
          from: aiMoveResponse.move.substring(0, 2),
          to: aiMoveResponse.move.substring(2, 4),
          piece: 'unknown', // Backend-ul nu returnează tipul piesei
          color: 'b',
          san: aiMoveResponse.san || aiMoveResponse.move,
          ai: true
        };
        
        setMoveHistory(prev => [...prev, moveObj]);
      }

      setIsAITurn(false);
      
      // Verifică starea jocului
      if (aiMoveResponse.checkmate) {
        setGameOver(true);
        setStatus('Checkmate! Black (AI) wins!');
      } else if (aiMoveResponse.draw) {
        setGameOver(true);
        setStatus('Draw!');
      } else if (aiMoveResponse.check) {
        setStatus('Check! White is in check. Your move.');
      } else {
        setStatus('Your turn (White).');
      }

      // Verifică dacă AI-ul poate face schimburi de ostatici
      setTimeout(async () => {
        await checkAIExchange();
      }, 500);

    } catch (error) {
      console.error('Error making AI move:', error);
      setStatus('AI move failed. Your turn.');
      setIsAITurn(false);
    }
  };

  // Funcție pentru verificarea și executarea schimburilor AI
  const checkAIExchange = async () => {
    if (!vsAI || !gameId || currentPlayer !== 'b') return;

    try {
      const exchangeResponse = await aiService.aiExchangeHostage(gameId);
      
      if (exchangeResponse.action === 'exchange') {
        // Actualizează ostaticii și rezervele după schimb
        setHostages(exchangeResponse.hostages);
        setReserves(exchangeResponse.reserves);
        setCurrentPlayer(exchangeResponse.turn);
        
        setStatus(`AI exchanged ${getPieceName(exchangeResponse.ai_exchanged.type)} for ${getPieceName(exchangeResponse.received.type)}. Your turn.`);
      }
    } catch (error) {
      console.error('Error checking AI exchange:', error);
    }
  };

  const handleHostageSelect = (index) => {
    if (gameOver || isAITurn) return;
    if (vsAI && currentPlayer !== playerColor) return; // Doar jucătorul uman poate selecta
    
    const selectedHostage = hostages[currentPlayer][index];
    setSelectedPiece(selectedHostage);
    setSelectedHostageIndex(index);
    setMode('exchange');
    setStatus(`Select a piece to exchange for ${getPieceName(selectedHostage.type)}`);
  };

  const handleReserveSelect = (index) => {
    if (gameOver || isAITurn) return;
    if (vsAI && currentPlayer !== playerColor) return; // Doar jucătorul uman poate selecta
    
    const selectedReserve = reserves[currentPlayer][index];
    setSelectedPiece(selectedReserve);
    setSelectedHostageIndex(index);
    setMode('drop');
    setStatus(`Select a square to drop ${getPieceName(selectedReserve.type)}`);
  };

  const handleExchangeSelect = (index) => {
    if (mode !== 'exchange' || !selectedPiece) return;
    if (vsAI && currentPlayer !== playerColor) return; // Doar jucătorul uman poate face schimburi
    
    const targetHostage = hostages[currentPlayer === 'w' ? 'b' : 'w'][index];
    if (pieceValues[selectedPiece.type] >= pieceValues[targetHostage.type]) {
      const newHostages = { ...hostages };
      newHostages[currentPlayer].splice(selectedHostageIndex, 1);
      const opponentColor = currentPlayer === 'w' ? 'b' : 'w';
      const exchangedPiece = newHostages[opponentColor][index];
      newHostages[opponentColor].splice(index, 1);
      const newReserves = { ...reserves };
      newReserves[currentPlayer].push({ type: exchangedPiece.type, color: currentPlayer });
      setHostages(newHostages);
      setReserves(newReserves);
      setMode('normal');
      setSelectedPiece(null);
      setSelectedHostageIndex(null);
      setStatus(`You exchanged a piece. ${vsAI ? 'AI to move.' : (currentPlayer === 'w' ? 'Black' : 'White') + ' to move.'}`);
      
      if (!vsAI) {
        setCurrentPlayer(currentPlayer === 'w' ? 'b' : 'w');
      } else {
        // În modul AI, după schimbul jucătorului, AI-ul poate face mutarea
        setCurrentPlayer('b');
        setIsAITurn(true);
        setTimeout(async () => {
          await makeAIMove();
        }, 1000);
      }
    } else {
      setStatus(`Invalid exchange. Your ${getPieceName(selectedPiece.type)} is not valuable enough.`);
      setMode('normal');
      setSelectedPiece(null);
      setSelectedHostageIndex(null);
    }
  };

  const getPieceName = (type) => {
    const pieceNames = { 'p': 'Pawn', 'n': 'Knight', 'b': 'Bishop', 'r': 'Rook', 'q': 'Queen', 'k': 'King' };
    return pieceNames[type];
  };

  const checkGameStatus = () => {
    if (game.isCheckmate()) {
      setGameOver(true);
      const winner = currentPlayer === 'w' ? 'Black' : 'White';
      setStatus(`Checkmate! ${winner} wins!`);
    } else if (game.isDraw()) {
      setGameOver(true);
      setStatus('Draw!');
    } else if (game.isCheck()) {
      const playerInCheck = currentPlayer === 'w' ? 'White' : 'Black';
      setStatus(`Check! ${playerInCheck} is in check.`);
    } else {
      if (vsAI) {
        setStatus(currentPlayer === playerColor ? 'Your turn (White).' : 'AI thinking...');
      } else {
        setStatus(`${currentPlayer === 'w' ? 'White' : 'Black'} to move.`);
      }
    }
  };

  const renderBoard = () => {
    const squares = [];
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    const ranks = ['8', '7', '6', '5', '4', '3', '2', '1'];

    for (let r = 0; r < 8; r++) {
     squares.push(<div key={`corner-bottom-${r}`} className="label corner"></div>);

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
            {piece && <div className="piece">{renderPiece(piece.type, piece.color)}</div>}
          </div>
        );
      }
      squares.push(<div key="corner-bottom" className="label corner"></div>);
    }
    for (let f = -1; f < 8; f++) {
      squares.push(<div key={`bottom-${files[f]}`} className="label file">{files[f]}</div>);
    }

    return <div className="board">{squares}</div>;
  };

  const renderPiece = (type, color) => {
    const pieceImagePaths = {
      'p': color === 'w' ? pionAlb : pionNegru,
      'n': color === 'w' ? caluAlb : caluNegru,
      'b': color === 'w' ? nebunuAlb : nebunuNegru,
      'r': color === 'w' ? turaAlba : turaNeagra,
      'q': color === 'w' ? reginaAlba : reginaNeagra,
      'k': color === 'w' ? regeAlb : regeNegru
    };
    return <img src={pieceImagePaths[type]} alt={`${color}${type}`} className="chess-piece" />;
  };

  const renderHostages = (color) => {
    return (
      <div className={`hostages hostages-${color}`}>
        <h3>{color === 'w' ? 'White Hostages' : 'Black Hostages'}</h3>
        <div className="hostages-list">
          {hostages[color].map((piece, index) => (
            <div
              key={index}
              className={`hostage ${mode === 'exchange' && currentPlayer !== color && (!vsAI || currentPlayer === playerColor) ? 'exchange-target' : ''}`}
              onClick={() => {
                if (mode === 'exchange' && currentPlayer !== color && (!vsAI || currentPlayer === playerColor)) {
                  handleExchangeSelect(index);
                } else if (currentPlayer === color && (!vsAI || currentPlayer === playerColor)) {
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

  const renderReserves = (color) => (
    <div className={`reserves reserves-${color}`}>
      <h3>{color === 'w' ? 'White Reserves' : 'Black Reserves'}</h3>
      <div className="reserves-list">
        {reserves[color].map((piece, index) => (
          <div
            key={index}
            className={`reserve ${currentPlayer === color && (!vsAI || currentPlayer === playerColor) ? 'active' : ''}`}
            onClick={() => currentPlayer === color && (!vsAI || currentPlayer === playerColor) && handleReserveSelect(index)}
            title={getPieceName(piece.type)}
          >
            {renderPiece(piece.type, piece.color)}
          </div>
        ))}
      </div>
    </div>
  );

  const renderMoveHistory = () => (
    <div className="move-history">
      <h3>Move History</h3>
      <div className="move-list">
        {moveHistory.map((move, index) => (
          <div key={index} className={`move ${move.ai ? 'ai-move' : ''}`}>
            {index % 2 === 0 ? `${Math.floor(index / 2) + 1}. ` : ''}
            {move.san}
            {move.captured ? ` (${getPieceName(move.captured)} captured)` : ''}
            {move.ai ? ' (AI)' : ''}
          </div>
        ))}
      </div>
    </div>
  );

  const renderGameInfo = () => (
    <div className="game-info">
      <div className="status">{status}</div>
      {vsAI && (
        <div className="ai-info">
          <p>You play as White, AI plays as Black</p>
          <p>Difficulty: {aiDifficulty}</p>
        </div>
      )}
      <div className="buttons">
        <button className="reset-button" onClick={resetGame} disabled={isAITurn}>
          Reset Game
        </button>
        <button className="mode-button" onClick={() => {
          setMode('normal');
          setSelectedPiece(null);
          setLegalMoveSquare(null);
          setSelectedHostageIndex(null);
          setSelectedSquare(null);
        }} disabled={isAITurn}>
          Cancel Selection
        </button>
        <button className="mode-button" onClick={() => {
          setGameStarted(false);
          setGameMode(null);
        }} style={{ backgroundColor: '#2196F3' }} disabled={isAITurn}>
          Back to Home
        </button>
      </div>
      {renderMoveHistory()}
    </div>
  );

  return (
    <div className="App">
      {!gameStarted ? (
        <HomePage onGameStart={handleGameStart} />
      ) : (
        <>
          <h1>Hostage Chess</h1>
          <div className="game-container">
            <div className="left-panel">
              {renderHostages('b')}
              {renderReserves('w')}
            </div>
            <div className="center-panel">
              <div className="board-container">{renderBoard()}</div>
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