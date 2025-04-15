import numpy as np
from functools import wraps
from typing import Tuple, List, Optional, Callable

#The game boundaries and limits
INFINITY_POS = float("inf")
INFINITY_NEG = -float("inf")
MAX_BOUNDARY = (INFINITY_POS, INFINITY_POS)
MIN_BOUNDARY = (INFINITY_NEG, INFINITY_NEG)

# the decorators to track how much time a method takes to run
def track_analysis_time(method):

    #Decorator to track time spent on position analysis
    @wraps(method)
    def timed_analysis(*args, **kwargs):
        import time
        start = time.time()
        result = method(*args, **kwargs)
        end = time.time()
        instance = args[0]
        if hasattr(instance, 'analysis_time'):
            instance.analysis_time += end - start
        return result
    return timed_analysis

def adaptive_depth_control(method):

    #Decoratos to adjust search depth based on game phase (when left with fewer pieces)
    @wraps(method)
    def depth_adjusted(*args, **kwargs):
        instance = args[0]
        position = args[1] if len(args) > 1 else None
        
        #increases the search depth when few pieces are left
        if position and (len(position.onyx_pieces) <= 4 or len(position.crystal_pieces) <= 4):
            instance.depth_ceiling += 1
            
        result = method(*args, **kwargs)
        
        #restore/resets to the original depth
        if position and (len(position.onyx_pieces) <= 4 or len(position.crystal_pieces) <= 4):
            instance.depth_ceiling -= 1
            
        return result
    return depth_adjusted

# class to calculate positional features for evaluation
class PositionEvaluator:
    #measures how far the peaces have moved/advanced
    
    @staticmethod
    def calculate_piece_advancement(positions: List[Tuple[int, int]], height: int, forward: bool) -> float:
        
        #measures how close the pieces are to each other
        if not positions:
            return 0
        return sum(pos[0] if forward else height - 1 - pos[0] for pos in positions)
    
    @staticmethod
    def evaluate_piece_coordination(positions: List[Tuple[int, int]]) -> float:
        #evaluates how well the pieces support each other
        if not positions:
            return 0
        coordination_score = 0
        for p1 in positions:
            for p2 in positions:
                if p1 != p2:
                    # Pieces within 2 squares support each other
                    if abs(p1[0] - p2[0]) <= 2 and abs(p1[1] - p2[1]) <= 2:
                        coordination_score += 0.5
        return coordination_score

    #measures how many pieces control the centere columns
    @staticmethod
    def evaluate_center_control(positions: List[Tuple[int, int]], width: int) -> float:
        if not positions:
            return 0
        center_score = 0
        center_columns = range(width // 4, 3 * width // 4)
        for pos in positions:
            if pos[1] in center_columns:
                center_score += 1
        return center_score

#function to compute the next position of the move
def calculate_move(start_pos, move_dir, player):
   
    row, col = start_pos
    if player == 1:  # Onyx pieces move down
        return (row + 1, col - 1) if move_dir == 1 else (row + 1, col) if move_dir == 2 else (row + 1, col + 1)
    else:  # Crystal pieces move up
        return (row - 1, col - 1) if move_dir == 1 else (row - 1, col) if move_dir == 2 else (row - 1, col + 1)

def switch_player(player):
    #Alternates between players Onyx (1) and Crystal (2).
    return 2 if player == 1 else 1

class GameMove:
    #represents a move in the game
    def __init__(self, position, move_dir, player):
        self.position = position
        self.move_dir = move_dir
        self.player = player

    def get_description(self):
        #provides details for logging
        return self.position, self.move_dir, self.player

    def get_row(self):
    #gets the row coordinates
        return self.position[0]

class TreeSearchAgent:
    #Game AI using enhanced Minimax tree search strategy with position evaluation.

    def __init__(self, board_config, player, search_depth, eval_func, variant=0):
        
        #Configures the search agent parameters.
        
           # board_config (list): Starting board layout
           # player (int): Current player (1=Onyx, 2=Crystal)
           # search_depth (int): Maximum search depth
           # eval_func (callable): Position evaluation method
           # variant (int): Game variant selector
       
        self.board_config = board_config
        self.player = player
        self.depth_ceiling = search_depth
        self.eval_func = eval_func
        self.variant = variant
        self.positions_analyzed = 0
        self.pieces_remaining = 0
        self.analysis_time = 0
        self.evaluator = PositionEvaluator()

#Main function to find the best move using minimax + evaluation
    @track_analysis_time
    @adaptive_depth_control
    def find_best_move(self):
        
        root_position = self._create_game_state()
        selected_move = None
        highest_score = INFINITY_NEG
        alpha = INFINITY_NEG
        beta = INFINITY_POS

        possible_moves = self._order_moves(root_position.available_actions(), root_position)
        
        #sortds and evaluates all legal moves
        for possible_move in possible_moves:
            self.positions_analyzed += 1
            next_position = root_position.transfer(possible_move)

            if next_position.isgoalstate():
                selected_move = possible_move
                break

            move_score = self.evaluate_opponent_moves(next_position, 1, alpha, beta)
            if move_score > highest_score:
                selected_move = possible_move
                highest_score = move_score
                alpha = max(alpha, highest_score)

        self._count_remaining_pieces(root_position, selected_move)
        return root_position.transfer(selected_move), self.positions_analyzed, self.pieces_remaining

#here it helps prioritize the better moves
    def _order_moves(self, moves, position):
        """Orders moves based on preliminary evaluation for better pruning"""
        def move_score(move):
            new_pos = calculate_move(move.position, move.move_dir, move.player)
            score = 0

            # prioritizes the captures
            if (move.player == 1 and new_pos in position.crystal_pieces) or \
               (move.player == 2 and new_pos in position.onyx_pieces):
                score += 10

            # prioritizes the center control
            if 2 <= new_pos[1] <= 5:
                score += 5

            # prioritizes the forward movement
            score += new_pos[0] if move.player == 1 else (7 - new_pos[0])
            return score
            
        return sorted(moves, key=move_score, reverse=True)

    @track_analysis_time
    def evaluate_player_moves(self, position, depth, alpha, beta):
        #Enhanced analysis of maximizing player's options
        if depth == self.depth_ceiling or position.isgoalstate():
            return self._evaluate_position(position)

        max_score = INFINITY_NEG
        moves = self._order_moves(position.available_actions(), position)

        for move in moves:
            self.positions_analyzed += 1
            score = self.evaluate_opponent_moves(position.transfer(move), depth + 1, alpha, beta)
            max_score = max(max_score, score)
            alpha = max(alpha, max_score)
            if alpha >= beta:
                break  # Beta cutoff
        return max_score

    @track_analysis_time
    def evaluate_opponent_moves(self, position, depth, alpha, beta):
        #Enhanced analysis of minimizing player's options
        if depth == self.depth_ceiling or position.isgoalstate():
            return self._evaluate_position(position)

        min_score = INFINITY_POS
        moves = self._order_moves(position.available_actions(), position)

        for move in moves:
            self.positions_analyzed += 1
            score = self.evaluate_player_moves(position.transfer(move), depth + 1, alpha, beta)
            min_score = min(min_score, score)
            beta = min(beta, min_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_score

    def _evaluate_position(self, position):
        """Comprehensive position evaluation incorporating multiple factors"""
        if position.isgoalstate():
            return INFINITY_POS if position.isgoalstate() == self.player else INFINITY_NEG

        # the base material and advancement evaluations
        score = position.utility(self.player)
        
        # add positional factors and center control evaluation
        if self.player == 1:
            score += (self.evaluator.evaluate_piece_coordination(position.onyx_pieces) -
                     self.evaluator.evaluate_piece_coordination(position.crystal_pieces))
            score += (self.evaluator.evaluate_center_control(position.onyx_pieces, position.width) -
                     self.evaluator.evaluate_center_control(position.crystal_pieces, position.width))
        else:
            score += (self.evaluator.evaluate_piece_coordination(position.crystal_pieces) -
                     self.evaluator.evaluate_piece_coordination(position.onyx_pieces))
            score += (self.evaluator.evaluate_center_control(position.crystal_pieces, position.width) -
                     self.evaluator.evaluate_center_control(position.onyx_pieces, position.width))
        
        return score

    def _create_game_state(self):
        #Initializes GameState object based on board configuration
        return GameState(
            board_config=self.board_config,
            player=self.player,
            eval_func=self.eval_func,
            height=5 if self.variant else 8,
            width=10 if self.variant else 8
        )

    def _count_remaining_pieces(self, position, move):
        #Updates on how many pieces are left for the opponent
        next_position = position.transfer(move)
        if self.player == 1:
            self.pieces_remaining = next_position.crystal_count
        else:
            self.pieces_remaining = next_position.onyx_count

class GameState:
    #represents current game configuration and available moves
    def __init__(self, board_config=None, onyx_pieces=None, crystal_pieces=None, 
                 onyx_count=0, crystal_count=0, player=1, eval_func=0, width=8, height=8):
        self.width = width
        self.height = height
        self.onyx_pieces = onyx_pieces or []
        self.crystal_pieces = crystal_pieces or []
        self.onyx_count = onyx_count
        self.crystal_count = crystal_count
        self.player = player
        self.eval_func = eval_func
        if board_config:
            self._setup_pieces(board_config)

    def _setup_pieces(self, board_config):
        #initializes piece positions based on the board matrix
        for i in range(self.height):
            for j in range(self.width):
                if board_config[i][j] == 1:
                    self.onyx_pieces.append((i, j))
                    self.onyx_count += 1
                elif board_config[i][j] == 2:
                    self.crystal_pieces.append((i, j))
                    self.crystal_count += 1

    def transfer(self, action):
       #applies an action to the current state and returns a new state
        onyx_pos = list(self.onyx_pieces)
        crystal_pos = list(self.crystal_pieces)

        if action.player == 1:  # Onyx move
            index = onyx_pos.index(action.position)
            new_pos = calculate_move(action.position, action.move_dir, action.player)
            onyx_pos[index] = new_pos
            if new_pos in crystal_pos:
                crystal_pos.remove(new_pos)

        elif action.player == 2:  # move for crystal
            index = crystal_pos.index(action.position)
            new_pos = calculate_move(action.position, action.move_dir, action.player)
            crystal_pos[index] = new_pos
            if new_pos in onyx_pos:
                onyx_pos.remove(new_pos)

        return GameState(
            onyx_pieces=onyx_pos,
            crystal_pieces=crystal_pos,
            onyx_count=len(onyx_pos),
            crystal_count=len(crystal_pos),
            player=switch_player(action.player),
            eval_func=self.eval_func,
            width=self.width,
            height=self.height
        )

    def available_actions(self):
        #Returns all VALID  actions for the current player
        actions = []
        positions = self.onyx_pieces if self.player == 1 else self.crystal_pieces

        for pos in sorted(positions, key=lambda p: (p[0], -p[1]) if self.player == 1 else (p[0], p[1])):
            for direction in [1, 2, 3]:  # checks for all possible directions
                new_pos = calculate_move(pos, direction, self.player)
                if self._is_valid_move(pos, new_pos):
                    actions.append(GameMove(pos, direction, self.player))
        return actions

    def _is_valid_move(self, current_pos, new_pos):
        #checks if move is valid
        row, col = new_pos
        return 0 <= row < self.height and 0 <= col < self.width and \
               new_pos not in self.onyx_pieces and new_pos not in self.crystal_pieces

    def utility(self, turn):
        #calculates the utility of the current state
        if self.eval_func == 0:
            return 0
        elif self.eval_func == 1:
            return self.offensive_function(turn)
        elif self.eval_func == 2:
            return self.defensive_function(turn)

    def isgoalstate(self):
        #determines if the current state is a goal state
        if any(pos[0] == self.height - 1 for pos in self.onyx_pieces) or not self.crystal_pieces:
            return 1
        if any(pos[0] == 0 for pos in self.crystal_pieces) or not self.onyx_pieces:
            return 2
        return 0
    
    def getMatrix(self):
        matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for item in self.onyx_pieces:
            matrix[item[0]][item[1]] = 1
        for item in self.crystal_pieces:
            matrix[item[0]][item[1]] = 2
        return matrix


    #Heuristic scoring functions are implemented here
    def offensive_function(self, turn):
        
        return 2 * self.myscore(turn) - self.enemyscore(turn)

    def defensive_function(self, turn):
        
        return self.myscore(turn) - 2 * self.enemyscore(turn)

    def myscore(self, turn):
     
        positions = self.onyx_pieces if turn == 1 else self.crystal_pieces
        return len(positions) + sum(pos[0] if turn == 1 else self.height - 1 - pos[0] for pos in positions)

    def enemyscore(self, turn):
        
        enemy_positions = self.crystal_pieces if turn == 1 else self.onyx_pieces
        return len(enemy_positions) + sum(pos[0] if turn == 2 else self.height - 1 - pos[0] for pos in enemy_positions)


#heuristics functions with empty placeholders, this can be customized
def OffensiveHeuristic1():
    pass

def DefensiveHeuristic1():
    pass

def OffensiveHeuristic2():
    pass

def DefensiveHeuristic2():
    pass