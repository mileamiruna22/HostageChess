# app.py - versiune corectată
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
        'last_move': None,
        'move_count': 0,  # Adăugat pentru debugging
        'game_status': 'active'  # Adăugat pentru tracking status
    }

@app.route('/new_game', methods=['POST'])
def new_game():
    game_id = str(random.randint(1000, 9999))
    games[game_id] = create_new_game()
    return jsonify({'game_id': game_id, 'fen': games[game_id]['board'].fen()}), 201

@app.route('/make_move', methods=['POST'])
def make_move():
    try:
        game_id = request.json.get('game_id')
        move_uci = request.json.get('move')

        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404

        game_state = games[game_id]
        board = game_state['board']
        
        # Verifică dacă jocul este încă activ
        if game_state.get('game_status') != 'active':
            return jsonify({'error': 'Game is not active'}), 400
        
        # Validare move format
        if not move_uci or len(move_uci) < 4:
            return jsonify({'error': 'Invalid move format'}), 400

        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError as e:
            return jsonify({'error': f'Invalid move format: {str(e)}'}), 400
        
        # Verifică dacă mutarea este legală
        if move not in board.legal_moves:
            return jsonify({'error': 'Invalid move - not in legal moves'}), 400

        # Salvează piesa capturată ÎNAINTE de mutare
        captured_piece = board.piece_at(move.to_square)
        
        # Execută mutarea
        board.push(move)
        game_state['move_count'] += 1
        
        # Actualizează ostaticii dacă a fost captură
        if captured_piece and captured_piece.piece_type != chess.KING:
            # CORECTARE: Culoarea care capturează este cea care tocmai a mutat
            capturing_color = 'w' if not board.turn else 'b'  # board.turn s-a schimbat după push
            captured_color = 'b' if capturing_color == 'w' else 'w'
            piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
            
            # Verifică că listele exist
            if capturing_color not in game_state['hostages']:
                game_state['hostages'][capturing_color] = []
                
            game_state['hostages'][capturing_color].append({
                'type': piece_type_char,
                'color': captured_color
            })
        
        game_state['last_move'] = move_uci
        
        # Verifică starea jocului
        game_over = False
        game_result = None
        
        if board.is_checkmate():
            game_over = True
            game_result = 'checkmate'
            game_state['game_status'] = 'finished'
        elif board.is_stalemate():
            game_over = True
            game_result = 'stalemate'
            game_state['game_status'] = 'finished'
        elif board.is_insufficient_material():
            game_over = True
            game_result = 'insufficient_material'
            game_state['game_status'] = 'finished'
        elif board.is_fifty_moves():
            game_over = True
            game_result = '50_moves'
            game_state['game_status'] = 'finished'
        
        return jsonify({
            'success': True,
            'fen': board.fen(),
            'hostages': game_state['hostages'],
            'reserves': game_state['reserves'],
            'turn': 'w' if board.turn else 'b',
            'check': board.is_check(),
            'checkmate': board.is_checkmate(),
            'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves(),
            'game_over': game_over,
            'game_result': game_result,
            'move_count': game_state['move_count']
        })
        
    except Exception as e:
        # Log eroarea pentru debugging
        print(f"Eroare în make_move: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/ai_move', methods=['POST'])
def ai_move():
    try:
        game_id = request.json.get('game_id')
        difficulty = request.json.get('difficulty', 'medium')

        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404

        game_state = games[game_id]
        board = game_state['board']

        # Verifică dacă jocul este activ
        if game_state.get('game_status') != 'active':
            return jsonify({'error': 'Game is not active'}), 400

        # Verifică dacă e rândul AI-ului (negru)
        if board.turn != chess.BLACK:
            return jsonify({'error': 'Not AI turn'}), 400

        # Verifică dacă există mutări legale
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return jsonify({'error': 'No legal moves available'}), 400

        # Setează dificultatea AI-ului
        old_depth = ai.depth
        try:
            if difficulty == 'easy':
                ai.depth = 2
            elif difficulty == 'medium':
                ai.depth = 3
            elif difficulty == 'hard':
                ai.depth = 4

            # Verifică mai întâi dacă AI-ul poate face un schimb avantajos de ostatici
            exchange_result = try_ai_hostage_exchange(game_state)
            if exchange_result.get('action') == 'exchange':
                return jsonify(exchange_result)

            # Dacă nu poate face schimb, încearcă să plaseze o piesă din rezerve
            drop_result = try_ai_piece_drop(game_state)
            if drop_result.get('action') == 'drop':
                return jsonify(drop_result)

            # Altfel, face o mutare normală
            best_move, move_value = ai.get_best_move(game_state)

            if best_move is None:
                # Încearcă o mutare aleatorie dacă AI-ul nu găsește nimic
                best_move = random.choice(legal_moves)

            # Salvează piesa capturată ÎNAINTE de mutare
            captured_piece = board.piece_at(best_move.to_square)
            
            # Execută mutarea
            board.push(best_move)
            game_state['move_count'] += 1

            # Actualizează ostaticii dacă a fost captură
            if captured_piece and captured_piece.piece_type != chess.KING:
                capturing_color = 'b'  # AI-ul e negru
                captured_color = 'w'   # Capturează piesele albe
                piece_type_char = 'pnbrqk'[captured_piece.piece_type - 1]
                
                if capturing_color not in game_state['hostages']:
                    game_state['hostages'][capturing_color] = []
                    
                game_state['hostages'][capturing_color].append({
                    'type': piece_type_char,
                    'color': captured_color
                })

            game_state['last_move'] = best_move.uci()

            # Calculează notația SAN pentru afișare (cu protecție la erori)
            move_san = best_move.uci()
            try:
                # Creează o copie temporară pentru a calcula SAN
                temp_board = chess.Board()
                temp_board.set_fen(board.fen())
                # Trebuie să calculăm SAN înainte de mutare
                temp_board = game_state['board'].copy()
                temp_board.pop()  # Anulează ultima mutare temporar
                move_san = temp_board.san(best_move)
            except Exception as san_error:
                print(f"Eroare la calcularea SAN: {san_error}")
                pass

            # Verifică starea jocului
            game_over = False
            game_result = None
            
            if board.is_checkmate():
                game_over = True
                game_result = 'checkmate'
                game_state['game_status'] = 'finished'
            elif board.is_stalemate():
                game_over = True
                game_result = 'stalemate'
                game_state['game_status'] = 'finished'
            elif board.is_insufficient_material():
                game_over = True
                game_result = 'insufficient_material'
                game_state['game_status'] = 'finished'
            elif board.is_fifty_moves():
                game_over = True
                game_result = '50_moves'
                game_state['game_status'] = 'finished'

            return jsonify({
                'success': True,
                'move': best_move.uci(),
                'san': move_san,
                'fen': board.fen(),
                'hostages': game_state['hostages'],
                'reserves': game_state['reserves'],
                'turn': 'w' if board.turn else 'b',
                'check': board.is_check(),
                'checkmate': board.is_checkmate(),
                'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves(),
                'game_over': game_over,
                'game_result': game_result,
                'move_count': game_state['move_count'],
                'move_value': move_value  # Pentru debugging
            })
            
        finally:
            # Restaurează adâncimea originală
            ai.depth = old_depth
            
    except Exception as e:
        print(f"Eroare în ai_move: {str(e)}")
        return jsonify({'error': f'AI move error: {str(e)}'}), 500

def try_ai_hostage_exchange(game_state):
    """Încearcă să facă un schimb avantajos de ostatici pentru AI"""
    try:
        board = game_state['board']
        ai_color = 'b'  # AI-ul joacă cu negru
        opponent_color = 'w'
        
        ai_hostages = game_state['hostages'].get(ai_color, [])
        opponent_hostages = game_state['hostages'].get(opponent_color, [])
        
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
            
            # Execută schimbul cu validare
            if ai_idx < len(game_state['hostages'][ai_color]):
                game_state['hostages'][ai_color].pop(ai_idx)
            if opp_idx < len(game_state['hostages'][opponent_color]):
                game_state['hostages'][opponent_color].pop(opp_idx)
            
            # Adaugă piesa primită în rezerve
            if ai_color not in game_state['reserves']:
                game_state['reserves'][ai_color] = []
                
            game_state['reserves'][ai_color].append({
                'type': opp_piece['type'],
                'color': ai_color
            })
            
            return {
                'action': 'exchange',
                'success': True,
                'ai_exchanged': ai_piece,
                'received': opp_piece,
                'hostages': game_state['hostages'],
                'reserves': game_state['reserves'],
                'turn': 'w',  # Trece rândul la jucător după schimb
                'message': f"AI a schimbat {get_piece_name(ai_piece['type'])} pentru {get_piece_name(opp_piece['type'])}"
            }
        
        return {'action': 'no_exchange', 'reason': 'No advantageous exchange found'}
        
    except Exception as e:
        print(f"Eroare în try_ai_hostage_exchange: {str(e)}")
        return {'action': 'no_exchange', 'reason': f'Exchange error: {str(e)}'}

def try_ai_piece_drop(game_state):
    """Încearcă să plaseze o piesă din rezerve pe tablă"""
    try:
        board = game_state['board']
        ai_color = 'b'  # AI-ul joacă cu negru
        
        ai_reserves = game_state['reserves'].get(ai_color, [])
        
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
        
        if best_piece_idx >= len(ai_reserves):
            return {'action': 'no_drop', 'reason': 'Invalid piece index'}
            
        selected_piece = ai_reserves[best_piece_idx]
        
        # Găsește o poziție strategică pentru plasare
        target_square = find_best_drop_square(board, selected_piece['type'], ai_color)
        
        if target_square:
            # Elimină piesa din rezerve
            game_state['reserves'][ai_color].pop(best_piece_idx)
            
            return {
                'action': 'drop',
                'success': True,
                'piece': selected_piece,
                'square': target_square,
                'reserves': game_state['reserves'],
                'turn': 'w',  # Trece rândul la jucător
                'message': f"AI a plasat {get_piece_name(selected_piece['type'])} pe {target_square}"
            }
        
        return {'action': 'no_drop', 'reason': 'No suitable squares for drop'}
        
    except Exception as e:
        print(f"Eroare în try_ai_piece_drop: {str(e)}")
        return {'action': 'no_drop', 'reason': f'Drop error: {str(e)}'}

def find_best_drop_square(board, piece_type, color):
    """Găsește cea mai bună poziție pentru plasarea unei piese"""
    try:
        # Pentru demonstrație, returnează o poziție validă goală
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
        
    except Exception as e:
        print(f"Eroare în find_best_drop_square: {str(e)}")
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
    try:
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
            'reserves': games[game_id]['reserves'],
            'success': True
        }

        # Dacă jucătorul e negru, AI-ul (alb) face prima mutare
        if player_color == 'b':
            old_depth = ai.depth
            try:
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
                    games[game_id]['move_count'] += 1
                    response_data['initial_ai_move'] = best_move.uci()
                    response_data['fen'] = games[game_id]['board'].fen()
            finally:
                ai.depth = old_depth

        return jsonify(response_data)
        
    except Exception as e:
        print(f"Eroare în new_ai_game: {str(e)}")
        return jsonify({'error': f'New game error: {str(e)}', 'success': False}), 500

@app.route('/game_status/<game_id>', methods=['GET'])
def get_game_status(game_id):
    """Endpoint pentru verificarea stării jocului"""
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game_state = games[game_id]
    board = game_state['board']
    
    return jsonify({
        'game_id': game_id,
        'fen': board.fen(),
        'hostages': game_state['hostages'],
        'reserves': game_state['reserves'],
        'turn': 'w' if board.turn else 'b',
        'check': board.is_check(),
        'checkmate': board.is_checkmate(),
        'draw': board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves(),
        'game_status': game_state.get('game_status', 'active'),
        'move_count': game_state.get('move_count', 0),
        'last_move': game_state.get('last_move')
    })

@app.route('/ai_exchange_hostage', methods=['POST'])
def ai_exchange_hostage():
    """Endpoint separat pentru schimbul de ostatici AI (opțional)"""
    try:
        game_id = request.json.get('game_id')

        if game_id not in games:
            return jsonify({'error': 'Game not found'}), 404

        game_state = games[game_id]
        result = try_ai_hostage_exchange(game_state)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Eroare în ai_exchange_hostage: {str(e)}")
        return jsonify({'error': f'Exchange error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)