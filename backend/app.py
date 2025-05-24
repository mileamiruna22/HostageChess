# app.py
from flask import Flask, request, jsonify
import chess
import random
from copy import deepcopy
from flask_cors import CORS
from minimax_ai import MinimaxAI

app = Flask(__name__)
CORS(app)

games = {}
ai = MinimaxAI(depth=3)

def create_new_game():
    return {
        'board': chess.Board(), 
        'hostages': {'w': [], 'b': []}, 
        'reserves': {'w': [], 'b': []},
        'turn_phase': 'normal',  # 'normal', 'exchange', 'drop'
        'last_move': None
    }

@app.route('/new_game', methods=['POST'])
def new_game():
    game_id = str(random.randint(1000, 9999))
    games[game_id] = create_new_game()
    return jsonify({'game_id': game_id, 'fen': games[game_id]['board'].fen()}), 201

@app.route('/make_move', methods=['POST'])
def make_move():
    game_id = request.json.get('game_id')
    move_uci = request.json.get('move')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]
    board = game_state['board']
    
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            captured_piece = board.piece_at(move.to_square)
            board.push(move)
            
            # Actualizează ostaticii dacă a fost captură
            if captured_piece and captured_piece.piece_type != chess.KING:
                capturing_color = 'w' if not board.turn else 'b'
                captured_color = 'b' if not board.turn else 'w'
                piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
                game_state['hostages'][capturing_color].append({
                    'type': piece_type_char,
                    'color': captured_color
                })
            
            game_state['last_move'] = move_uci
            
            return jsonify({
                'fen': board.fen(),
                'hostages': game_state['hostages'],
                'reserves': game_state['reserves'],
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
    board = game_state['board']

    # Verifică dacă e rândul AI-ului (negru)
    if board.turn != chess.BLACK:
        return jsonify({'error': 'Not AI turn'}), 400

    # Setează dificultatea AI-ului
    if difficulty == 'easy':
        ai.depth = 2
    elif difficulty == 'medium':
        ai.depth = 3
    elif difficulty == 'hard':
        ai.depth = 4

    # Verifică mai întâi dacă AI-ul poate face un schimb avantajos de ostatici
    exchange_result = try_ai_hostage_exchange(game_state)
    if exchange_result['action'] == 'exchange':
        return jsonify(exchange_result)

    # Dacă nu poate face schimb, încearcă să plaseze o piesă din rezerve
    drop_result = try_ai_piece_drop(game_state)
    if drop_result['action'] == 'drop':
        return jsonify(drop_result)

    # Altfel, face o mutare normală
    best_move, _ = ai.get_best_move(game_state)

    if best_move is None:
        return jsonify({'error': 'No legal moves available'}), 400

    # Execută mutarea
    captured_piece = board.piece_at(best_move.to_square)
    board.push(best_move)

    # Actualizează ostaticii dacă a fost captură
    if captured_piece and captured_piece.piece_type != chess.KING:
        capturing_color = 'b'  # AI-ul e negru
        captured_color = 'w'   # Capturează piesele albe
        piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
        game_state['hostages'][capturing_color].append({
            'type': piece_type_char,
            'color': captured_color
        })

    game_state['last_move'] = best_move.uci()

    # Calculează notația SAN pentru afișare
    move_san = best_move.uci()
    try:
        # Creează o copie temporară pentru a calcula SAN
        temp_board = chess.Board()
        temp_board.set_fen(game_state['board'].fen())
        move_san = temp_board.san(best_move)
    except:
        pass

    return jsonify({
        'move': best_move.uci(),
        'san': move_san,
        'fen': board.fen(),
        'hostages': game_state['hostages'],
        'reserves': game_state['reserves'],
        'turn': 'w' if board.turn else 'b',
        'check': board.is_check(),
        'checkmate': board.is_checkmate(),
        'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves()
    })

def try_ai_hostage_exchange(game_state):
    """Încearcă să facă un schimb avantajos de ostatici pentru AI"""
    board = game_state['board']
    ai_color = 'b'  # AI-ul joacă cu negru
    opponent_color = 'w'
    
    ai_hostages = game_state['hostages'][ai_color]
    opponent_hostages = game_state['hostages'][opponent_color]
    
    if not ai_hostages or not opponent_hostages:
        return {'action': 'no_exchange', 'reason': 'No hostages available'}
    
    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 100}
    
    best_exchange = None
    best_value = -1000
    
    for ai_idx, ai_hostage in enumerate(ai_hostages):
        ai_value = piece_values.get(ai_hostage['type'].lower(), 0)
        
        for opp_idx, opp_hostage in enumerate(opponent_hostages):
            opp_value = piece_values.get(opp_hostage['type'].lower(), 0)
            
            # AI-ul poate schimba doar dacă piesa sa are valoare >= cu cea a adversarului
            if ai_value >= opp_value:
                exchange_value = opp_value - ai_value
                
                if exchange_value > best_value:
                    best_value = exchange_value
                    best_exchange = (ai_idx, opp_idx, ai_hostage, opp_hostage)
    
    if best_exchange and best_value >= -2:  # Acceptă schimburi rezonabile
        ai_idx, opp_idx, ai_piece, opp_piece = best_exchange
        
        # Execută schimbul
        game_state['hostages'][ai_color].pop(ai_idx)
        game_state['hostages'][opponent_color].pop(opp_idx)
        
        # Adaugă piesa primită în rezerve
        game_state['reserves'][ai_color].append({
            'type': opp_piece['type'],
            'color': ai_color
        })
        
        return {
            'action': 'exchange',
            'ai_exchanged': ai_piece,
            'received': opp_piece,
            'hostages': game_state['hostages'],
            'reserves': game_state['reserves'],
            'turn': 'w',  # Trece rândul la jucător după schimb
            'message': f"AI exchanged {get_piece_name(ai_piece['type'])} for {get_piece_name(opp_piece['type'])}"
        }
    
    return {'action': 'no_exchange', 'reason': 'No advantageous exchange found'}

def try_ai_piece_drop(game_state):
    """Încearcă să plaseze o piesă din rezerve pe tablă"""
    board = game_state['board']
    ai_color = 'b'  # AI-ul joacă cu negru
    
    ai_reserves = game_state['reserves'][ai_color]
    
    if not ai_reserves:
        return {'action': 'no_drop', 'reason': 'No pieces in reserves'}
    
    # Alege cea mai valoroasă piesă din rezerve
    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9}
    best_piece_idx = 0
    best_value = 0
    
    for idx, piece in enumerate(ai_reserves):
        value = piece_values.get(piece['type'].lower(), 0)
        if value > best_value:
            best_value = value
            best_piece_idx = idx
    
    selected_piece = ai_reserves[best_piece_idx]
    
    # Găsește o poziție strategică pentru plasare
    target_square = find_best_drop_square(board, selected_piece['type'], ai_color)
    
    if target_square:
        # Plasează piesa (în realitate, aceasta ar trebui să fie gestionată de frontend)
        # Pentru acum, doar eliminăm piesa din rezerve și o marcăm ca plasată
        game_state['reserves'][ai_color].pop(best_piece_idx)
        
        return {
            'action': 'drop',
            'piece': selected_piece,
            'square': target_square,
            'reserves': game_state['reserves'],
            'turn': 'w',  # Trece rândul la jucător
            'message': f"AI dropped {get_piece_name(selected_piece['type'])} on {target_square}"
        }
    
    return {'action': 'no_drop', 'reason': 'No suitable squares for drop'}

def find_best_drop_square(board, piece_type, color):
    """Găsește cea mai bună poziție pentru plasarea unei piese"""
    # Pentru demonstrație, returnează o poziție validă goală
    # În implementarea reală, ar trebui să evalueze poziții strategice
    
    target_ranks = [1, 2] if color == 'b' else [6, 7]  # Rândurile aproape de baza AI-ului
    
    for rank in target_ranks:
        for file in range(8):
            square = chess.square(file, rank)
            if not board.piece_at(square):
                square_name = chess.square_name(square)
                return square_name
    
    # Dacă nu găsește în rândurile preferate, caută oriunde
    for square in chess.SQUARES:
        if not board.piece_at(square):
            return chess.square_name(square)
    
    return None

def get_piece_name(piece_type):
    """Returnează numele piesei în română"""
    names = {
        'p': 'Pion', 'n': 'Cal', 'b': 'Nebun', 
        'r': 'Tură', 'q': 'Regină', 'k': 'Rege'
    }
    return names.get(piece_type.lower(), 'Piesă necunoscută')

@app.route('/new_ai_game', methods=['POST'])
def new_ai_game():
    player_color = request.json.get('player_color', 'w')
    difficulty = request.json.get('difficulty', 'medium')

    game_id = str(random.randint(1000, 9999))
    games[game_id] = create_new_game()

    response_data = {
        'game_id': game_id,
        'fen': games[game_id]['board'].fen(),
        'player_color': player_color,
        'difficulty': difficulty,
        'hostages': games[game_id]['hostages'],
        'reserves': games[game_id]['reserves']
    }

    # Dacă jucătorul e negru, AI-ul (alb) face prima mutare
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
            games[game_id]['last_move'] = best_move.uci()
            response_data['initial_ai_move'] = best_move.uci()
            response_data['fen'] = games[game_id]['board'].fen()

    return jsonify(response_data)

@app.route('/ai_exchange_hostage', methods=['POST'])
def ai_exchange_hostage():
    """Endpoint separat pentru schimbul de ostatici AI (opțional)"""
    game_id = request.json.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]
    result = try_ai_hostage_exchange(game_state)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)