"""
Algoritm Minimax pentru Hostage Chess
Acest modul implementează algoritmul minimax cu alpha-beta pruning pentru jocul Hostage Chess.
"""
import chess
import random
from copy import deepcopy

class MinimaxAI:
    def __init__(self, depth=3):
        """
        Inițializează AI-ul cu o anumită adâncime de căutare.
        
        Args:
            depth (int): Adâncimea maximă de căutare în arborele de joc.
        """
        self.depth = depth
        self.piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 100
        }
        
        # Tabele de poziții pentru evaluarea poziției pieselor
        self.position_tables = {
            chess.PAWN: [
                0,  0,  0,  0,  0,  0,  0,  0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5,  5, 10, 25, 25, 10,  5,  5,
                0,  0,  0, 20, 20,  0,  0,  0,
                5, -5,-10,  0,  0,-10, -5,  5,
                5, 10, 10,-20,-20, 10, 10,  5,
                0,  0,  0,  0,  0,  0,  0,  0
            ],
            chess.KNIGHT: [
                -50,-40,-30,-30,-30,-30,-40,-50,
                -40,-20,  0,  0,  0,  0,-20,-40,
                -30,  0, 10, 15, 15, 10,  0,-30,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -30,  0, 15, 20, 20, 15,  0,-30,
                -30,  5, 10, 15, 15, 10,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-30,-30,-30,-40,-50
            ],
            chess.BISHOP: [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0, 10, 10, 10, 10,  0,-10,
                -10,  5,  5, 10, 10,  5,  5,-10,
                -10,  0,  5, 10, 10,  5,  0,-10,
                -10,  5,  5,  5,  5,  5,  5,-10,
                -10,  0,  5,  0,  0,  5,  0,-10,
                -20,-10,-10,-10,-10,-10,-10,-20
            ],
            chess.ROOK: [
                0,  0,  0,  0,  0,  0,  0,  0,
                5, 10, 10, 10, 10, 10, 10,  5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                -5,  0,  0,  0,  0,  0,  0, -5,
                0,  0,  0,  5,  5,  0,  0,  0
            ],
            chess.QUEEN: [
                -20,-10,-10, -5, -5,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0,  5,  5,  5,  5,  0,-10,
                -5,  0,  5,  5,  5,  5,  0, -5,
                0,  0,  5,  5,  5,  5,  0, -5,
                -10,  5,  5,  5,  5,  5,  0,-10,
                -10,  0,  5,  0,  0,  0,  0,-10,
                -20,-10,-10, -5, -5,-10,-10,-20
            ],
            chess.KING: [
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -30,-40,-40,-50,-50,-40,-40,-30,
                -20,-30,-30,-40,-40,-30,-30,-20,
                -10,-20,-20,-20,-20,-20,-20,-10,
                20, 20,  0,  0,  0,  0, 20, 20,
                20, 30, 10,  0,  0, 10, 30, 20
            ]
        }
        
    def get_best_move(self, game_state):
        """
        Determină cea mai bună mutare pentru starea curentă a jocului folosind algoritmul minimax.
        
        Args:
            game_state (dict): Starea jocului curent, conținând tabla și ostaticii.
            
        Returns:
            tuple: (mutarea cea mai bună (în format chess.Move), valoarea acesteia)
        """
        board = game_state['board']
        hostages = game_state['hostages']
        is_maximizing = board.turn  # True pentru alb, False pentru negru
        
        best_move = None
        best_value = float('-inf') if is_maximizing else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Generează toate mutările posibile
        legal_moves = list(board.legal_moves)
        
        # Amestecă mutările pentru a adăuga variație
        random.shuffle(legal_moves)
        
        for move in legal_moves:
            # Creează o copie a stării jocului pentru simulare
            new_board = board.copy()
            new_hostages = deepcopy(hostages)
            
            # Verifică dacă este o captură pentru a actualiza ostaticii
            is_capture = new_board.is_capture(move)
            captured_piece = None
            
            if is_capture:
                target_square = move.to_square
                captured_piece = new_board.piece_at(target_square)
                capturing_color = 'w' if new_board.turn else 'b'
                captured_color = 'b' if new_board.turn else 'w'
                
                if captured_piece and captured_piece.piece_type != chess.KING:
                    new_hostages[capturing_color].append({
                        'type': self._piece_type_to_char(captured_piece.piece_type),
                        'color': captured_color
                    })
            
            # Execută mutarea pe tabla copiată
            new_board.push(move)
            
            # Apelează minimax recursiv
            new_game_state = {'board': new_board, 'hostages': new_hostages}
            value = self._minimax(new_game_state, self.depth - 1, alpha, beta, not is_maximizing)
            
            # Actualizează cea mai bună mutare
            if is_maximizing:
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
            else:
                if value < best_value:
                    best_value = value
                    best_move = move
                beta = min(beta, best_value)
            
            # Alpha-beta pruning
            if beta <= alpha:
                break
        
        return best_move, best_value
    
    def _minimax(self, game_state, depth, alpha, beta, is_maximizing):
        """
        Implementarea recursivă a algoritmului minimax cu alpha-beta pruning.
        
        Args:
            game_state (dict): Starea curentă a jocului.
            depth (int): Adâncimea rămasă pentru căutare.
            alpha (float): Valoarea alpha pentru pruning.
            beta (float): Valoarea beta pentru pruning.
            is_maximizing (bool): True dacă jucătorul curent maximizează scorul, False altfel.
            
        Returns:
            float: Valoarea cea mai bună pentru poziția curentă.
        """
        board = game_state['board']
        hostages = game_state['hostages']
        
        # Verifică condițiile de bază pentru oprirea recursiei
        if depth == 0 or board.is_game_over():
            return self._evaluate_position(game_state)
            
        if is_maximizing:
            value = float('-inf')
            for move in board.legal_moves:
                # Creează o copie a stării jocului pentru simulare
                new_board = board.copy()
                new_hostages = deepcopy(hostages)
                
                # Verifică dacă este o captură pentru a actualiza ostaticii
                is_capture = new_board.is_capture(move)
                captured_piece = None
                
                if is_capture:
                    target_square = move.to_square
                    captured_piece = new_board.piece_at(target_square)
                    capturing_color = 'w' if new_board.turn else 'b'
                    captured_color = 'b' if new_board.turn else 'w'
                    
                    if captured_piece and captured_piece.piece_type != chess.KING:
                        new_hostages[capturing_color].append({
                            'type': self._piece_type_to_char(captured_piece.piece_type),
                            'color': captured_color
                        })
                
                # Execută mutarea pe tabla copiată
                new_board.push(move)
                
                # Apelează minimax recursiv
                new_game_state = {'board': new_board, 'hostages': new_hostages}
                value = max(value, self._minimax(new_game_state, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            for move in board.legal_moves:
                # Creează o copie a stării jocului pentru simulare
                new_board = board.copy()
                new_hostages = deepcopy(hostages)
                
                # Verifică dacă este o captură pentru a actualiza ostaticii
                is_capture = new_board.is_capture(move)
                captured_piece = None
                
                if is_capture:
                    target_square = move.to_square
                    captured_piece = new_board.piece_at(target_square)
                    capturing_color = 'w' if new_board.turn else 'b'
                    captured_color = 'b' if new_board.turn else 'w'
                    
                    if captured_piece and captured_piece.piece_type != chess.KING:
                        new_hostages[capturing_color].append({
                            'type': self._piece_type_to_char(captured_piece.piece_type),
                            'color': captured_color
                        })
                
                # Execută mutarea pe tabla copiată
                new_board.push(move)
                
                # Apelează minimax recursiv
                new_game_state = {'board': new_board, 'hostages': new_hostages}
                value = min(value, self._minimax(new_game_state, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
            return value
    
    def _evaluate_position(self, game_state):
        """
        Evaluează starea jocului și returnează un scor.
        Valorile pozitive favorizează albul, cele negative favorizează negrul.
        
        Args:
            game_state (dict): Starea jocului curent.
            
        Returns:
            float: Scorul evaluat pentru poziția curentă.
        """
        board = game_state['board']
        hostages = game_state['hostages']
        
        # Verifică dacă jocul s-a terminat
        if board.is_checkmate():
            return float('inf') if not board.turn else float('-inf')
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_fifty_moves() or board.is_repetition(3):
            return 0.0
        
        # Evaluează materiale pe tablă
        material_score = self._evaluate_material(board)
        
        # Evaluează pozițiile pieselor
        position_score = self._evaluate_piece_positions(board)
        
        # Evaluează ostaticii
        hostage_score = self._evaluate_hostages(hostages)
        
        # Evaluarea șahului
        check_score = 0.5 if board.is_check() else 0
        if board.turn:  # White's turn
            check_score = -check_score
        
        # Evaluează mobilitatea (numărul de mutări legale)
        mobility_score = self._evaluate_mobility(board)
        
        # Combină scorurile cu ponderi
        total_score = (
            material_score +
            position_score * 0.1 +
            hostage_score +
            check_score +
            mobility_score * 0.1
        )
        
        return total_score
    
    def _evaluate_material(self, board):
        """
        Evaluează valoarea materialului de pe tablă.
        
        Args:
            board (chess.Board): Tabla de șah.
            
        Returns:
            float: Scorul materialului (pozitiv pentru alb, negativ pentru negru).
        """
        score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.piece_values[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value
        
        return score
    
    def _evaluate_piece_positions(self, board):
        """
        Evaluează poziționarea pieselor pe tablă.
        
        Args:
            board (chess.Board): Tabla de șah.
            
        Returns:
            float: Scorul poziționării pieselor.
        """
        score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                position_value = 0
                # Obține valoarea pentru poziție din tabelele de poziții
                if piece.piece_type in self.position_tables:
                    # Inversează indicele poziției pentru piesele negre
                    if piece.color == chess.WHITE:
                        position_index = square
                    else:
                        position_index = 63 - square
                    
                    position_value = self.position_tables[piece.piece_type][position_index]
                
                if piece.color == chess.WHITE:
                    score += position_value
                else:
                    score -= position_value
        
        return score
    
    def _evaluate_hostages(self, hostages):
        """
        Evaluează ostaticii capturați de fiecare parte.
        
        Args:
            hostages (dict): Dicționar cu ostaticii.
            
        Returns:
            float: Scorul ostaticilor.
        """
        score = 0.0
        
        # Evaluează ostaticii albi capturați de negru
        for hostage in hostages['b']:
            piece_type_char = hostage['type'].lower()
            piece_type = self._char_to_piece_type(piece_type_char)
            score -= self.piece_values[piece_type]
        
        # Evaluează ostaticii negri capturați de alb
        for hostage in hostages['w']:
            piece_type_char = hostage['type'].lower()
            piece_type = self._char_to_piece_type(piece_type_char)
            score += self.piece_values[piece_type]
        
        return score
    
    def _evaluate_mobility(self, board):
        """
        Evaluează mobilitatea (numărul de mutări legale).
        
        Args:
            board (chess.Board): Tabla de șah.
            
        Returns:
            float: Scorul de mobilitate.
        """
        # Salvează tura curentă
        original_turn = board.turn
        
        # Calculează mobilitatea pentru alb
        board.turn = chess.WHITE
        white_mobility = len(list(board.legal_moves))
        
        # Calculează mobilitatea pentru negru
        board.turn = chess.BLACK
        black_mobility = len(list(board.legal_moves))
        
        # Restaurează tura originală
        board.turn = original_turn
        
        return white_mobility - black_mobility
    
    def _piece_type_to_char(self, piece_type):
        """
        Convertește un tip de piesă în caracterul său corespunzător.
        
        Args:
            piece_type (int): Tipul piesei din biblioteca chess.
            
        Returns:
            str: Caracterul corespunzător piesei ('p', 'n', 'b', 'r', 'q', 'k').
        """
        mapping = {
            chess.PAWN: 'p',
            chess.KNIGHT: 'n',
            chess.BISHOP: 'b',
            chess.ROOK: 'r',
            chess.QUEEN: 'q',
            chess.KING: 'k'
        }
        return mapping.get(piece_type, '?')
    
    def _char_to_piece_type(self, char):
        """
        Convertește un caracter de piesă în tipul său corespunzător.
        
        Args:
            char (str): Caracterul piesei ('p', 'n', 'b', 'r', 'q', 'k').
            
        Returns:
            int: Tipul piesei din biblioteca chess.
        """
        mapping = {
            'p': chess.PAWN,
            'n': chess.KNIGHT,
            'b': chess.BISHOP,
            'r': chess.ROOK,
            'q': chess.QUEEN,
            'k': chess.KING
        }
        return mapping.get(char.lower(), chess.PAWN)