from flask import Flask, request, jsonify
import chess

app = Flask(__name__)
board = chess.Board()

@app.route('/move', methods=['POST'])
def move():
    move = request.json['move']
    try:
        board.push_san(move)
        return jsonify({'board': board.fen()})
    except ValueError:
        return jsonify({'error': 'Mutare invalidă'}), 400

if __name__ == '__main__':
    app.run(debug=True)