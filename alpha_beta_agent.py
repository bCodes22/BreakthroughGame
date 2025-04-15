from minimax_agent import * 
from minimax_agent import State
 #importing utilities and classes from minimax_agent

#simple constants for  the score boundaries
MAX_SCORE = float('inf')
MIN_SCORE = float('-inf')

def timing_wrapper(func):
    #a simple timing decorator
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        args[0].search_time += end - start
        return result
    return wrapper

class ImprovedSearchAgent:

    #a chess-like game AI using alpha-beta pruning
    def __init__(self, board, current_player, max_depth, scoring_func, board_type=0):
        self.board = board
        self.current_player = current_player
        self.max_depth = max_depth #sets the alpha-beta search depth
        self.scoring_func = scoring_func
        self.board_type = board_type
        self.nodes_visited = 0
        self.pieces_left = 0
        self.search_time = 0
        
        #the pieces values and position weights
        self.piece_value = 100
        self.center_bonus = 10
        self.advance_bonus = 5

    @timing_wrapper
    def get_best_move(self):
        #finds the best moves using alpha-beta search
        game_state = self._init_game_state()
        best_move = None
        best_score = MIN_SCORE
        
        #searches the variables
        alpha = MIN_SCORE
        beta = MAX_SCORE
        
        #gets sorted moves for better pruning of the algorithm
        moves = self._sort_moves(game_state.available_actions(), game_state)

        for move in moves:
            self.nodes_visited += 1
            next_state = game_state.transfer(move)

            #early exit on the winning move
            if next_state.isgoalstate():
                best_move = move
                break

            #searches deeper
            score = self._min_search(next_state, 1, alpha, beta)
            if score > best_score:
                best_move = move
                best_score = score
                alpha = max(alpha, best_score)

        # updates the piece count and return
        self._update_pieces(game_state, best_move)
        return game_state.transfer(best_move), self.nodes_visited, self.pieces_left

    def _sort_moves(self, moves, state):
        #Sorts the  moves to improve pruning chances
        def move_value(m):
            new_pos = single_move(m.coordinate, m.direction, m.turn) # type: ignore
            value = 0
            
            #captures the moves
            if m.turn == 1 and new_pos in state.white_positions:
                value += self.piece_value
            elif m.turn == 2 and new_pos in state.black_positions:
                value += self.piece_value
                
            #center columns control
            if 2 <= new_pos[1] <= 5:
                value += self.center_bonus
                
            # a forward progress   
            value += self.advance_bonus * (new_pos[0] if m.turn == 1 else 7 - new_pos[0])
            
            return value

        return sorted(moves, key=move_value, reverse=True)

    def _max_search(self, state, depth, alpha, beta):
        
        #alpha-beta maximizing search
        if depth >= self.max_depth or state.isgoalstate():
            return self._evaluate_position(state)

        value = MIN_SCORE
        moves = self._sort_moves(state.available_actions(), state)

        for move in moves:
            self.nodes_visited += 1
            value = max(value, self._min_search(state.transfer(move), depth + 1, alpha, beta))
            
            if value >= beta:  #Beta cutoff
                return value
            alpha = max(alpha, value)

        return value

    def _min_search(self, state, depth, alpha, beta):
        
        #alpha-beta minimizing search
        if depth >= self.max_depth or state.isgoalstate():
            return self._evaluate_position(state)

        value = MAX_SCORE
        moves = self._sort_moves(state.available_actions(), state)

        for move in moves:
            self.nodes_visited += 1
            value = min(value, self._max_search(state.transfer(move), depth + 1, alpha, beta))
            
            if value <= alpha:  # Alpha cutoff
                return value
            beta = min(beta, value)

        return value

    def _evaluate_position(self, state):
        #Scores the current position
        if state.isgoalstate():
            return MAX_SCORE if state.isgoalstate() == self.current_player else MIN_SCORE

        #gets the base score from utility
        score = state.utility(self.current_player)

        #adds the positional bonuses
        if self.current_player == 1:
            pieces = state.black_positions
            enemy_pieces = state.white_positions
        else:
            pieces = state.white_positions
            enemy_pieces = state.black_positions

        #controls center column 
        score += sum(self.center_bonus for pos in pieces if 2 <= pos[1] <= 5)
        score -= sum(self.center_bonus for pos in enemy_pieces if 2 <= pos[1] <= 5)

        # Forward progress
        if self.current_player == 1:
            score += sum(self.advance_bonus * pos[0] for pos in pieces)
            score -= sum(self.advance_bonus * (7 - pos[0]) for pos in enemy_pieces)
        else:
            score += sum(self.advance_bonus * (7 - pos[0]) for pos in pieces)
            score -= sum(self.advance_bonus * pos[0] for pos in enemy_pieces)

        return score

    def _init_game_state(self):
        #Set up initial game state
        if self.board_type == 0:
            return State(boardmatrix=self.board, turn=self.current_player, function=self.scoring_func)
        return State(boardmatrix=self.board, turn=self.current_player, function=self.scoring_func, 
                    height=5, width=10)

    def _update_pieces(self, state, move):
        #tracks the remaining pieces after a move
        next_state = state.transfer(move)
        self.pieces_left = (next_state.white_num if self.current_player == 1 
                           else next_state.black_num)
