"""
Algoritm Minimax îmbunătățit pentru Hostage Chess
Acest modul implementează algoritmul minimax cu alpha-beta pruning specializat pentru Hostage Chess.
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
        
        # Tabele de poziții îmbunătățite pentru Hostage Chess
        self.position_tables = {
            chess.PAWN: [
                0,  0,  0,  0,  0,  0,  0,  0,
                60, 60, 60, 60, 60, 60, 60, 60,  # Pionii avansați sunt foarte valoroși
                15, 15, 25, 35, 35, 25, 15, 15,
                8,  8, 15, 30, 30, 15,  8,  8,
                5,  5, 10, 25, 25, 10,  5,  5,
                0,  0,  0, 20, 20,  0,  0,  0,
                5, -5,-10,  0,  0,-10, -5,  5,
                0,  0,  0,  0,  0,  0,  0,  0
            ],
            chess.KNIGHT: [
                -50,-40,-30,-25,-25,-30,-40,-50,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -25,  0, 15, 25, 25, 15,  0,-25,  # Centrul tablei e mai valoros
                -25,  0, 15, 25, 25, 15,  0,-25,
                -30,  5, 15, 20, 20, 15,  5,-30,
                -40,-20,  0,  5,  5,  0,-20,-40,
                -50,-40,-30,-25,-25,-30,-40,-50
            ],
            chess.BISHOP: [
                -20,-10,-10,-10,-10,-10,-10,-20,
                -10,  0,  0,  0,  0,  0,  0,-10,
                -10,  0, 10, 15, 15, 10,  0,-10,
                -10,  5, 10, 15, 15, 10,  5,-10,
                -10,  0, 10, 15, 15, 10,  0,-10,
                -10, 10, 10, 10, 10, 10, 10,-10,
                -10,  5,  0,  0,  0,  0,  5,-10,
                -20,-10,-10,-10,-10,-10,-10,-20
            ],
            chess.ROOK: [
                5,  5,  5,  5,  5,  5,  5,  5,
                10, 15, 15, 15, 15, 15, 15, 10,  # Turile active sunt valoroase
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
                -50,-40,-40,-50,-50,-40,-40,-50,
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
        Determină cea mai bună mutare pentru starea curentă a jocului.
        
        Args:
            game_state (dict): Starea jocului curent.
            
        Returns:
            tuple: (mutarea cea mai bună, valoarea acesteia)
        """
        board = game_state['board']
        is_maximizing = board.turn == chess.WHITE
        
        best_move = None
        best_value = float('-inf') if is_maximizing else float('inf')
        alpha = float('-inf')
        beta = float('inf')
        
        # Generează toate mutările posibile și le sortează pentru o căutare mai eficientă
        legal_moves = list(board.legal_moves)
        legal_moves = self._order_moves(board, legal_moves)
        
        for move in legal_moves:
            # Creează o copie a stării jocului pentru simulare
            new_game_state = self._make_move_copy(game_state, move)
            
            # Apelează minimax recursiv
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
    
    def _order_moves(self, board, moves):
        """
        Sortează mutările pentru a optimiza alpha-beta pruning.
        Mutările de captură și cele care dau șah sunt evaluate primele.
        """
        def move_priority(move):
            priority = 0
            
            # Capturări au prioritate mare
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    priority += self.piece_values[captured_piece.piece_type]
                    
                # Capturările cu piese mai puțin valoroase sunt preferate
                moving_piece = board.piece_at(move.from_square)
                if moving_piece:
                    priority -= self.piece_values[moving_piece.piece_type] * 0.1
            
            # Mutările care dau șah au prioritate
            board_copy = board.copy()
            board_copy.push(move)
            if board_copy.is_check():
                priority += 50
                
            # Mutările către centru au prioritate mică
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            center_distance = abs(3.5 - to_file) + abs(3.5 - to_rank)
            priority -= center_distance
            
            return -priority  # Sortare descrescătoare
        
        return sorted(moves, key=move_priority)
    
    def _make_move_copy(self, game_state, move):
        """
        Creează o copie a stării jocului și execută mutarea pe ea.
        """
        new_game_state = {
            'board': game_state['board'].copy(),
            'hostages': deepcopy(game_state['hostages']),
            'reserves': deepcopy(game_state['reserves']),
            'turn_phase': game_state.get('turn_phase', 'normal'),
            'last_move': game_state.get('last_move', None)
        }
        
        board = new_game_state['board']
        
        # Verifică dacă este captură pentru actualizarea ostaticilor
        is_capture = board.is_capture(move)
        captured_piece = None
        
        if is_capture:
            captured_piece = board.piece_at(move.to_square)
            if captured_piece and captured_piece.piece_type != chess.KING:
                capturing_color = 'w' if board.turn else 'b'
                captured_color = 'b' if board.turn else 'w'
                
                new_game_state['hostages'][capturing_color].append({
                    'type': self._piece_type_to_char(captured_piece.piece_type),
                    'color': captured_color
                })
        
        # Execută mutarea
        board.push(move)
        new_game_state['last_move'] = move.uci()
        
        return new_game_state
    
    def _minimax(self, game_state, depth, alpha, beta, is_maximizing):
        """
        Implementarea recursivă a algoritmului minimax cu alpha-beta pruning.
        """
        board = game_state['board']
        
        # Verifică condițiile de bază pentru oprirea recursiei
        if depth == 0 or board.is_game_over():
            return self._evaluate_position(game_state)
            
        if is_maximizing:
            value = float('-inf')
            legal_moves = self._order_moves(board, list(board.legal_moves))
            
            for move in legal_moves:
                new_game_state = self._make_move_copy(game_state, move)
                value = max(value, self._minimax(new_game_state, depth - 1, alpha, beta, False))
                alpha = max(alpha, value)
                
                if beta <= alpha:
                    break
            return value
        else:
            value = float('inf')
            legal_moves = self._order_moves(board, list(board.legal_moves))
            
            for move in legal_moves:
                new_game_state = self._make_move_copy(game_state, move)
                value = min(value, self._minimax(new_game_state, depth - 1, alpha, beta, True))
                beta = min(beta, value)
                
                if beta <= alpha:
                    break
            return value
    
    def _evaluate_position(self, game_state):
        """
        Evaluează starea jocului specializat pentru Hostage Chess.
        """
        board = game_state['board']
        hostages = game_state['hostages']
        reserves = game_state['reserves']
        
        # Verifică dacă jocul s-a terminat
        if board.is_checkmate():
            return 10000 if board.turn == chess.BLACK else -10000
        elif board.is_stalemate() or board.is_insufficient_material():
            return 0.0
        
        score = 0.0
        
        # 1. Evaluarea materialului pe tablă (40% din scor)
        score += self._evaluate_material(board) * 0.4
        
        # 2. Evaluarea pozițiilor pieselor (15% din scor)
        score += self._evaluate_piece_positions(board) * 0.15
        
        # 3. Evaluarea ostaticilor (25% din scor) - FOARTE IMPORTANT în Hostage Chess
        score += self._evaluate_hostages(hostages) * 0.25
        
        # 4. Evaluarea rezervelor (15% din scor) - Nou pentru Hostage Chess
        score += self._evaluate_reserves(reserves) * 0.15
        
        # 5. Evaluarea mobilității (5% din scor)
        score += self._evaluate_mobility(board) * 0.05
        
        # 6. Bonus pentru șah și amenințări
        if board.is_check():
            score += 30 if board.turn == chess.BLACK else -30
        
        # 7. Evaluarea controlului centrului
        score += self._evaluate_center_control(board)
        
        return score
    
    def _evaluate_material(self, board):
        """Evaluează materialul de pe tablă."""
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
        """Evaluează poziționarea pieselor."""
        score = 0.0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type in self.position_tables:
                position_index = square if piece.color == chess.WHITE else 63 - square
                position_value = self.position_tables[piece.piece_type][position_index]
                
                if piece.color == chess.WHITE:
                    score += position_value
                else:
                    score -= position_value
        
        return score
    
    def _evaluate_hostages(self, hostages):
        """
        Evaluează ostaticii - aspect cheie în Hostage Chess.
        Ostaticii pot fi schimbați pentru piese din rezerve.
        """
        score = 0.0
        
        # Evaluează ostaticii albi capturați de negru (avantaj pentru negru)
        for hostage in hostages['b']:
            piece_type = self._char_to_piece_type(hostage['type'])
            value = self.piece_values[piece_type]
            score -= value  # Negativ pentru alb
        
        # Evaluează ostaticii negri capturați de alb (avantaj pentru alb)
        for hostage in hostages['w']:
            piece_type = self._char_to_piece_type(hostage['type'])
            value = self.piece_values[piece_type]
            score += value  # Pozitiv pentru alb
        
        return score
    
    def _evaluate_reserves(self, reserves):
        """
        Evaluează rezervele - piese care pot fi plasate pe tablă.
        Rezervele sunt foarte valoroase în Hostage Chess.
        """
        score = 0.0
        
        # Evaluează rezervele albe (avantaj pentru alb)
        for reserve in reserves['w']:
            piece_type = self._char_to_piece_type(reserve['type'])
            value = self.piece_values[piece_type]
            score += value * 1.2  # Rezervele sunt mai valoroase decât piesele normale
        
        # Evaluează rezervele negre (avantaj pentru negru)
        for reserve in reserves['b']:
            piece_type = self._char_to_piece_type(reserve['type'])
            value = self.piece_values[piece_type]
            score -= value * 1.2  # Negativ pentru alb
        
        return score
    
    def _evaluate_mobility(self, board):
        """Evaluează mobilitatea pieselor."""
        white_moves = len(list(board.legal_moves)) if board.turn == chess.WHITE else 0
        
        # Schimbă rândul pentru a evalua mutările negrului
        board.turn = not board.turn
        black_moves = len(list(board.legal_moves)) if board.turn == chess.BLACK else 0
        board.turn = not board.turn  # Restaurează rândul original
        
        return (white_moves - black_moves) * 0.1
    
    def _evaluate_center_control(self, board):
        """Evaluează controlul centrului tablei."""
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        score = 0.0
        
        for square in center_squares:
            piece = board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    score += 10
                else:
                    score -= 10
        
        return score
    
    def _piece_type_to_char(self, piece_type):
        """Convertește tipul de piesă în caracter."""
        conversion = {
            chess.PAWN: 'p',
            chess.KNIGHT: 'n', 
            chess.BISHOP: 'b',
            chess.ROOK: 'r',
            chess.QUEEN: 'q',
            chess.KING: 'k'
        }
        return conversion.get(piece_type, 'p')
    
    def _char_to_piece_type(self, char):
        """Convertește caracterul în tipul de piesă."""
        conversion = {
            'p': chess.PAWN,
            'n': chess.KNIGHT,
            'b': chess.BISHOP, 
            'r': chess.ROOK,
            'q': chess.QUEEN,
            'k': chess.KING
        }
        return conversion.get(char.lower(), chess.PAWN)
    
    def should_make_hostage_exchange(self, game_state, ai_color='b'):
        """
        Determină dacă AI-ul ar trebui să facă un schimb de ostatici.
        """
        hostages = game_state['hostages']
        ai_hostages = hostages.get(ai_color, [])
        opponent_hostages = hostages.get('w' if ai_color == 'b' else 'b', [])
        
        if not ai_hostages or not opponent_hostages:
            return None
        
        # Caută cel mai avantajos schimb
        best_exchange = None
        best_value = -1000
        
        for ai_idx, ai_hostage in enumerate(ai_hostages):
            ai_value = self.piece_values[self._char_to_piece_type(ai_hostage['type'])]
            
            for opp_idx, opp_hostage in enumerate(opponent_hostages):
                opp_value = self.piece_values[self._char_to_piece_type(opp_hostage['type'])]
                
                # AI-ul acceptă doar schimburi egale sau avantajoase
                if ai_value <= opp_value:
                    exchange_value = opp_value - ai_value
                    
                    if exchange_value > best_value:
                        best_value = exchange_value
                        best_exchange = {
                            'ai_idx': ai_idx,
                            'opp_idx': opp_idx,
                            'ai_piece': ai_hostage,
                            'opp_piece': opp_hostage,
                            'value': exchange_value
                        }
        
        # Acceptă schimbul dacă e avantajos sau cel puțin egal
        if best_exchange and best_value >= 0:
            return best_exchange
            
        return None
    
    def get_best_reserve_placement(self, game_state, ai_color='b'):
        """
        Determină cea mai bună plasare pentru o piesă din rezerve.
        """
        reserves = game_state['reserves'].get(ai_color, [])
        if not reserves:
            return None
        
        board = game_state['board']
        
        # Alege cea mai valoroasă piesă din rezerve
        best_piece_idx = 0
        best_piece_value = 0
        
        for idx, piece in enumerate(reserves):
            value = self.piece_values[self._char_to_piece_type(piece['type'])]
            if value > best_piece_value:
                best_piece_value = value
                best_piece_idx = idx
        
        selected_piece = reserves[best_piece_idx]
        
        # Găsește cea mai bună poziție strategică
        best_square = self._find_best_placement_square(board, selected_piece['type'], ai_color)
        
        if best_square:
            return {
                'piece_idx': best_piece_idx,
                'piece': selected_piece,
                'square': best_square
            }
        
        return None
    
    def _find_best_placement_square(self, board, piece_type, color):
        """
        Găsește cea mai bună poziție pentru plasarea unei piese din rezerve.
        """
        # Prioritizează pozițiile în funcție de tipul piesei și strategia AI-ului
        if color == 'b':  # AI-ul e negru
            preferred_ranks = [2, 3, 1]  # Prefer rândurile din mijloc și aproape de bază
        else:
            preferred_ranks = [5, 4, 6]
        
        best_square = None
        best_score = -1000
        
        for rank in preferred_ranks:
            for file in range(8):
                square = chess.square(file, rank)
                
                # Verifică dacă pătratul e liber
                if not board.piece_at(square):
                    square_score = self._evaluate_placement_square(board, square, piece_type, color)
                    
                    if square_score > best_score:
                        best_score = square_score
                        best_square = chess.square_name(square)
        
        return best_square
    
    def _evaluate_placement_square(self, board, square, piece_type, color):
        """
        Evaluează cât de bună este o poziție pentru plasarea unei piese.
        """
        score = 0.0
        
        # Bonus pentru centru
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        center_distance = abs(3.5 - file) + abs(3.5 - rank)
        score -= center_distance * 5
        
        # Bonus pentru protecția altor piese
        for adj_square in [square + 8, square - 8, square + 1, square - 1]:
            if 0 <= adj_square <= 63:
                piece = board.piece_at(adj_square)
                if piece and piece.color == (chess.WHITE if color == 'w' else chess.BLACK):
                    score += 10
        
        # Bonus pentru atacarea pieselor inamice
        # (aceasta ar trebui extinsă pentru fiecare tip de piesă)
        
        return score