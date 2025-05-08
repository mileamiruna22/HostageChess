from flask import Flask, request, jsonify
import chess

app = Flask(__name__)
games = {}

def create_new_game():
    """Creează o nouă stare a jocului."""
    return {
        'board': chess.Board(),
        'hostages': {'w': [], 'b': []},
        'current_player': 'w'
    }

@app.route('/new_game', methods=['POST'])
def new_game():
    """Creează un nou joc și returnează un ID."""
    game_id = 'default_game' # Simplu pentru un singur joc
    games[game_id] = create_new_game()
    return jsonify({'game_id': game_id, 'fen': games[game_id]['board'].fen()})

@app.route('/move', methods=['POST'])
def move():
    game_id = request.json.get('game_id')
    move_san = request.json.get('move')
    take_hostage = request.json.get('take_hostage', False)

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]
    board = game_state['board']
    current_player = board.turn.name

    try:
        move = board.parse_san(move_san)
        captured_piece = board.piece_at(move.to_square)
        board.push(move)

        if captured_piece and take_hostage:
            capturing_color = current_player
            game_state['hostages'][capturing_color].append(captured_piece.symbol())

        return jsonify({
            'fen': board.fen(),
            'hostages': game_state['hostages'],
            'turn': board.turn.name
        })
    except ValueError:
        return jsonify({'error': 'Mutare invalidă'}), 400

@app.route('/release_hostage', methods=['POST'])
def release_hostage():
    game_id = request.json.get('game_id')
    hostage_type = request.json.get('hostage_type')
    hostage_color = request.json.get('hostage_color')
    release_square = request.json.get('release_square')
    releasing_piece_to = request.json.get('releasing_piece_to')
    releasing_piece_from = request.json.get('releasing_piece_from')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    game_state = games[game_id]
    board = game_state['board']
    current_player = board.turn.name

    if current_player != releasing_piece_from[0]: # Verifică dacă jucătorul care eliberează este cel al cărui este tura
        return jsonify({'error': 'Not your turn'}), 400

    # Verifică dacă ostaticul este în lista jucătorului
    try:
        hostage_index = game_state['hostages'][current_player].index(hostage_type)
    except ValueError:
        return jsonify({'error': 'Hostage not found'}), 400

    # Verifică dacă câmpul de reintrare este pe prima linie și este liber
    if not chess.square_name(chess.parse_square(release_square))[1] == ('1' if current_player == 'w' else '8'):
        return jsonify({'error': 'Release square is not on your first rank'}), 400
    if board.piece_at(chess.parse_square(release_square)) is not None:
        return jsonify({'error': 'Release square is occupied'}), 400

    # Verifică dacă piesa care a mutat este adiacentă primei linii
    releasing_square_rank = int(chess.square_name(chess.parse_square(releasing_piece_to))[1])
    first_rank = 1 if current_player == 'w' else 8
    if not (releasing_square_rank == first_rank or releasing_square_rank == first_rank + (-1 if current_player == 'w' else 1)):
        return jsonify({'error': 'Releasing piece is not adjacent to your first rank'}), 400

    # Efectuează eliberarea
    piece_symbol = hostage_type.lower() if hostage_color == 'b' else hostage_type.upper()
    board.set_piece_at(chess.parse_square(release_square), chess.Piece.from_symbol(piece_symbol))
    del game_state['hostages'][current_player][hostage_index]
    board.turn = chess.WHITE if current_player == 'b' else chess.BLACK # Schimbă tura
    game_state['current_player'] = 'w' if current_player == 'b' else 'b'

    return jsonify({
        'fen': board.fen(),
        'hostages': game_state['hostages'],
        'turn': board.turn.name
    })

if __name__ == '__main__':
    app.run(debug=True)