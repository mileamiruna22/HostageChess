# app.py
from flask import Flask, request, jsonify
import chess
import random
from copy import deepcopy
from flask_cors import CORS  # Importăm CORS
from minimax_ai import MinimaxAI

app = Flask(__name__)
CORS(app)  # Activăm CORS pentru toate rutele

games = {}
ai = MinimaxAI(depth=3)

def create_new_game():
    return {'board': chess.Board(), 'hostages': {'w': [], 'b': []}, 'reserves': {'w': [], 'b': []}}

@app.route('/new_game', methods=['POST'])
def new_game():
    # Aici va veni logica ta pentru crearea unui joc nou (dacă nu ai deja implementată)
    game_id = str(random.randint(1000, 9999))
    games[game_id] = create_new_game()
    return jsonify({'game_id': game_id, 'fen': games[game_id]['board'].fen()}), 201

@app.route('/make_move', methods=['POST'])
def make_move():
    game_id = request.json.get('game_id')
    move_uci = request.json.get('move')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    board = games[game_id]['board']
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            captured_piece = board.piece_at(move.to_square)
            board.push(move)
            if captured_piece and captured_piece.piece_type != chess.KING:
                capturing_color = 'w' if not board.turn else 'b'
                captured_color = 'b' if not board.turn else 'w'
                piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
                games[game_id]['hostages'][capturing_color].append({
                    'type': piece_type_char,
                    'color': captured_color
                })
            return jsonify({
                'fen': board.fen(),
                'hostages': games[game_id]['hostages'],
                'turn': 'w' if board.turn else 'b',
                'check': board.is_check(),
                'checkmate': board.is_checkmate(),
                'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves()
            })
        else:
            return jsonify({'error': 'Invalid move'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid move format'}), 400

@app.route('/ai_move', methods=['POST'])
def ai_move():
    game_id = request.json.get('game_id')
    difficulty = request.json.get('difficulty', 'medium')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]

    if difficulty == 'easy':
        ai.depth = 2
    elif difficulty == 'medium':
        ai.depth = 3
    elif difficulty == 'hard':
        ai.depth = 4

    best_move, _ = ai.get_best_move(game_state)

    if best_move is None:
        return jsonify({'error': 'No legal moves available'}), 400

    board = game_state['board']

    captured_piece = board.piece_at(best_move.to_square)
    board.push(best_move)

    if captured_piece and captured_piece.piece_type != chess.KING:
        capturing_color = 'w' if not board.turn else 'b'
        captured_color = 'b' if not board.turn else 'w'
        piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
        game_state['hostages'][capturing_color].append({
            'type': piece_type_char,
            'color': captured_color
        })

    # Calculăm notația SAN pentru a o returna
    move_san = best_move.uci()  # Folosim UCI dacă SAN nu este disponibil
    try:
        # Încercăm să obținem notația SAN - poate fi nevoie de o mutare inversă și recalculare
        temp_board = chess.Board(game_state['board'].fen())
        temp_board.push(best_move)
        move_san = temp_board.san(best_move)
    except Exception as e:
        print(f"Error calculating SAN notation: {e}")
        
    return jsonify({
        'move': best_move.uci(),
        'san': move_san,
        'fen': board.fen(),
        'hostages': game_state['hostages'],
        'turn': 'w' if board.turn else 'b',
        'check': board.is_check(),
        'checkmate': board.is_checkmate(),
        'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves()
    })

@app.route('/new_ai_game', methods=['POST'])
def new_ai_game():
    player_color = request.json.get('player_color', 'w')
    difficulty = request.json.get('difficulty', 'medium')

    game_id = str(random.randint(1000, 9999))  # Generăm un ID unic
    games[game_id] = create_new_game()

    response_data = {
        'game_id': game_id,
        'fen': games[game_id]['board'].fen(),
        'player_color': player_color,
        'difficulty': difficulty
    }

    if player_color == 'b':
        if difficulty == 'easy':
            ai.depth = 2
        elif difficulty == 'medium':
            ai.depth = 3
        elif difficulty == 'hard':
            ai.depth = 4

        best_move, _ = ai.get_best_move(games[game_id])

        if best_move:
            games[game_id]['board'].push(best_move)
            response_data['initial_ai_move'] = best_move.uci()
            response_data['fen'] = games[game_id]['board'].fen()

    return jsonify(response_data)

@app.route('/ai_exchange_hostage', methods=['POST'])
def ai_exchange_hostage():
    game_id = request.json.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]
    board = game_state['board']

    ai_color = 'b' if board.turn == chess.BLACK else 'w'

    if not game_state['hostages'][ai_color]:
        return jsonify({'error': 'AI has no hostages to exchange'}), 400

    opponent_color = 'w' if ai_color == 'b' else 'b'

    if not game_state['hostages'][opponent_color]:
        return jsonify({'error': 'No opponent hostages available to exchange'}), 400

    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 100}

    ai_hostages = sorted(game_state['hostages'][ai_color],
                        key=lambda p: piece_values.get(p['type'].lower(), 0))

    opponent_hostages = sorted(game_state['hostages'][opponent_color],
                                 key=lambda p: piece_values.get(p['type'].lower(), 0))

    best_exchange = None

    for ai_hostage_idx, ai_hostage in enumerate(ai_hostages):
        ai_value = piece_values.get(ai_hostage['type'].lower(), 0)

        for opp_hostage_idx, opp_hostage in enumerate(opponent_hostages):
            opp_value = piece_values.get(opp_hostage['type'].lower(), 0)

            if ai_value >= opp_value:
                exchange_value = opp_value - ai_value

                if best_exchange is None or exchange_value > best_exchange[0]:
                    best_exchange = (exchange_value, ai_hostage_idx, opp_hostage_idx)

    if best_exchange:
        _, ai_idx, opp_idx = best_exchange

        ai_piece = game_state['hostages'][ai_color][ai_idx]
        opp_piece = game_state['hostages'][opponent_color][opp_idx]

        ai_piece_removed = game_state['hostages'][ai_color].pop(ai_idx)
        opp_piece_removed = game_state['hostages'][opponent_color].pop(opp_idx)

        game_state['reserves'][ai_color].append({
            'type': opp_piece_removed['type'],
            'color': ai_color
        })

        game_state['board'].turn = not game_state['board'].turn

        return jsonify({
            'action': 'exchange',
            'ai_exchanged': {
                'type': ai_piece_removed['type'],
                'color': ai_piece_removed['color']
            },
            'received': {
                'type': opp_piece_removed['type'],
                'color': opp_piece_removed['color']
            },
            'hostages': game_state['hostages'],
            'reserves': game_state['reserves'],
            'turn': 'w' if game_state['board'].turn else 'b'
        })

    return jsonify({
        'action': 'no_exchange',
        'reason': 'No advantageous exchange found',
        'turn': 'w' if game_state['board'].turn else 'b'
    })

if __name__ == '__main__':
    app.run(debug=True)