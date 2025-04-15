import numpy as np
import pygame
import sys, os, math
import time
import random

# the initial representation of the board:
# 1 = Dark Piece, 
# 2 = Light Piece, 
# 0 = Empty Cell
gameMatrix = [[1, 1, 1, 1, 1, 1, 1, 1],
                                [1, 1, 1, 1, 1, 1, 1, 1],
                                [0, 0, 0, 0, 0, 0, 0, 0],
                                [0, 0, 0, 0, 0, 0, 0, 0],
                                [0, 0, 0, 0, 0, 0, 0, 0],
                                [0, 0, 0, 0, 0, 0, 0, 0],
                                [2, 2, 2, 2, 2, 2, 2, 2],
                                [2, 2, 2, 2, 2, 2, 2, 2]]

#constants for evaluation functions and boundaries, values for points
MAX_LIMIT = float("inf")
MIN_LIMIT = -float("inf")
MAX_PAIR = (MAX_LIMIT, MAX_LIMIT)
MIN_PAIR = (MIN_LIMIT, MIN_LIMIT)

#calculates a single move given a position, direction, and turn based on player
def calculate_move(start_pos, move_dir, player):
    if player == 1:  #the black pieces move down
        if move_dir == 1:
            return start_pos[0] + 1, start_pos[1] - 1
        elif move_dir == 2:
            return start_pos[0] + 1, start_pos[1]
        elif move_dir == 3:
            return start_pos[0] + 1, start_pos[1] + 1
        
    elif player == 2:  # the white pieces move up
        if move_dir == 1:
            return start_pos[0] - 1, start_pos[1] - 1
        elif move_dir == 2:
            return start_pos[0] - 1, start_pos[1]
        elif move_dir == 3:
            return start_pos[0] - 1, start_pos[1] + 1

# Alternates the player's turn
def alterturn(turn):
 #switches the turn 1 -> 2, and 2-> 1
    return 2 if turn == 1 else 1

# Represents a single action taken by a piece
class Action:
    def __init__(self, coordinate, direction, turn):
        self.coordinate = coordinate #coordinate, The starting position of the piece
        self.direction = direction #direction, the direction of the move (1, 2, or 3)
        self.turn = turn #turn, the player's turn (1 for blac, 2 for white)

    def getString(self):
       #gets back a string representation of the move
        return self.coordinate, self.direction, self.turn

    def getCoordinate_x(self):
    #gets x-coordinate
        return self.coordinate[0]

#represents the game state, including the board and pieces
class State:
    def __init__(self,
                 BoardRepresentation=None,
                 BlackPiecePosition=None,
                 WhitePiecePosition=None,
                 black_num=0,
                 white_num=0,
                 turn=1,
                 function=0,
                 width=8,
                 height=8):
       
        #here it shows the game representations
        self.width = width
        self.height = height
        self.BlackPiecePositions = BlackPiecePosition or []
        self.WhitePiecePositions = WhitePiecePosition or []
        self.black_num = black_num
        self.white_num = white_num
        self.turn = turn
        self.function = function

        #initializes the positions from the board if  is provided
        if BoardRepresentation is not None:
            for i in range(self.height):
                for j in range(self.width):
                    if BoardRepresentation[i][j] == 1:
                        self.BlackPiecePositions.append((i, j))
                        self.black_num += 1
                    elif BoardRepresentation[i][j] == 2:
                        self.WhitePiecePositions.append((i, j))
                        self.white_num += 1

    def transfer(self, action):
        #executes an action and returns the resulting state.
        black_pos = list(self.BlackPiecePositions)
        white_pos = list(self.WhitePiecePositions)

        if action.turn == 1:  # Black player's move
            if action.coordinate in self.BlackPiecePositions:
                index = black_pos.index(action.coordinate)
                new_pos = calculate_move(action.coordinate, action.direction, action.turn)
                black_pos[index] = new_pos
                if new_pos in self.WhitePiecePositions:  #captures the opponent's piece
                    white_pos.remove(new_pos)
            else:
                print("Invalid action!")

        elif action.turn == 2:  # White player's move
            if action.coordinate in self.WhitePiecePositions:
                index = white_pos.index(action.coordinate)
                new_pos = calculate_move(action.coordinate, action.direction, action.turn)
                white_pos[index] = new_pos
                if new_pos in self.BlackPiecePositions:  # capture sopponent's piece
                    black_pos.remove(new_pos)
            else:
                print("Invalid action!")

        # creates and return the new state
        return State(BlackPiecePosition=black_pos, WhitePiecePosition=white_pos, 
                     black_num=self.black_num, white_num=self.white_num,
                     turn=alterturn(action.turn), function=self.function, 
                     height=self.height, width=self.width)

    def available_actions(self):
        #returns all possible actions for the current player
        available_actions = []

        if self.turn == 1:  # Black player's turn
            for pos in sorted(self.BlackPiecePositions, key=lambda p: (p[0], -p[1]), reverse=True):

                #checks for possible moves such as 
                #diagonal left, straight forward, diagonal right
                if pos[0] != self.height - 1 and pos[1] != 0 and (pos[0] + 1, pos[1] - 1) not in self.BlackPiecePositions:
                    available_actions.append(Action(pos, 1, 1))
                if pos[0] != self.height - 1 and (pos[0] + 1, pos[1]) not in self.BlackPiecePositions and (pos[0] + 1, pos[1]) not in self.WhitePiecePositions:
                    available_actions.append(Action(pos, 2, 1))
                if pos[0] != self.height - 1 and pos[1] != self.width - 1 and (pos[0] + 1, pos[1] + 1) not in self.BlackPiecePositions:
                    available_actions.append(Action(pos, 3, 1))

        elif self.turn == 2:  # White player's turn
            for pos in sorted(self.WhitePiecePositions, key=lambda p: (p[0], p[1])):

                #checks the possible moves 
                # diagonal left, straight forward, diagonal right
                if pos[0] != 0 and pos[1] != 0 and (pos[0] - 1, pos[1] - 1) not in self.WhitePiecePositions:
                    available_actions.append(Action(pos, 1, 2))
                if pos[0] != 0 and (pos[0] - 1, pos[1]) not in self.BlackPiecePositions and (pos[0] - 1, pos[1]) not in self.WhitePiecePositions:
                    available_actions.append(Action(pos, 2, 2))
                if pos[0] != 0 and pos[1] != self.width - 1 and (pos[0] - 1, pos[1] + 1) not in self.WhitePiecePositions:
                    available_actions.append(Action(pos, 3, 2))

        return available_actions

    def getMatrix(self):
       #converts the current state to a matrix representation
        matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for item in self.BlackPiecePositions:
            matrix[item[0]][item[1]] = 1
        for item in self.WhitePiecePositions:
            matrix[item[0]][item[1]] = 2
        return matrix

    def utility(self, turn):
        
        #here it computes the utility value based on the evaluation function
        if self.function == 0:
            return 0
        elif self.function == 1:
            return self.offensiveHeuristic1(turn)
        elif self.function == 2:
            return self.defensiveHeuristic1(turn)
        elif self.function == 3:
            return self.offensiveHeuristic2(turn)
        elif self.function == 4:
            return self.defensiveHeuristic2(turn)

    def winningscore(self, turn):
        winningvalue = 200
        if turn == 1:
            if self.isgoalstate() == 1:
                return winningvalue
            elif self.isgoalstate() == 2:
                return -winningvalue
            else:
                return 0
        elif turn == 2:
            if self.isgoalstate() == 2:
                return winningvalue
            elif self.isgoalstate() == 1:
                return -winningvalue
            else:
                return 0

    def isgoalstate(self, type=0):
        #a stadard rule to check if the game is won by either player
        if type == 0:
            #if any white piece reaches the top row or black has no pieces left → White wins (returns 2)
            if 0 in [item[0] for item in self.WhitePiecePositions] or len(self.BlackPiecePositions) == 0:
                return 2
            #if any black piece reaches the top row or white has no pieces left → black wins (returns 1)
            if self.height - 1 in [item[0] for item in self.BlackPiecePositions] or len(self.WhitePiecePositions) == 0:
                return 1
            #game will continue of none of the above conditions are met
            return 0
        else:
            count = 0 #counts how many black pieces reached the bottom row
            for i in self.BlackPiecePositions:
                if i[0] == 7:
                    count += 1
            if count == 3:
                return True
            count = 0 #counts the number of white pieces that reaches the bottom row
            for i in self.WhitePiecePositions:
                if i[0] == 0:
                    count += 1
            if count == 3:
                return True
            #so if either player has 2 or fewer peices left, the game ends
            if len(self.BlackPiecePositions) <= 2 or len(self.WhitePiecePositions) <= 2:
                return True
            #no end condition is met
        return False


    def myScore(self, turn):
        if turn == 1:
            return len(self.BlackPiecePositions) \
                   + sum(pos[0] for pos in self.BlackPiecePositions)

        elif turn == 2:
            return len(self.WhitePiecePositions) \
                   + sum(7 - pos[0] for pos in self.WhitePiecePositions)


    def opponentScore(self, turn):
        if turn == 1:
            return len(self.WhitePiecePositions) \
                   + sum(7 - pos[0] for pos in self.WhitePiecePositions)

        elif turn == 2:
            return len(self.BlackPiecePositions) \
                   + sum(pos[0] for pos in self.BlackPiecePositions)
            

    def offensiveHeuristic1(self, turn):
        return 2*(30-self.opponentScore(turn))+random.random()/10               

    def defensiveHeuristic1(self, turn):
        return 2*self.myScore(turn)+random.random()/10
               
    def offensiveHeuristic2(self, turn):
        return 1 * self.myScore(turn) - 2 * self.opponentScore(turn)

    def defensiveHeuristic2(self, turn):
        return 2 * self.myScore(turn) - 2 * self.opponentScore(turn)
class MinimaxAgent:
    
    def __init__(self, BoardRepresentation, turn, depth, function, type=0):
        self.BoardRepresentation = BoardRepresentation
        self.turn = turn
        self.maxdepth = depth
        self.function = function
        self.type = type
        self.blocks = 0
        self.piece_num = 0


    def max_value(self, state, depth):
        if depth == self.maxdepth or state.isgoalstate() != 0:
            return state.utility(self.turn)
        v = MIN_LIMIT
        for action in state.available_actions():
            v = max(v, self.min_value(state.transfer(action), depth + 1))
            self.blocks += 1
        return v

    def min_value(self, state, depth):
        if depth == self.maxdepth or state.isgoalstate() != 0:
            return state.utility(self.turn)
        v = MAX_LIMIT
        for action in state.available_actions():
            v = min(v, self.max_value(state.transfer(action), depth + 1))
            self.blocks += 1

        return v

    def minimax_decision(self):
        final_action = None
        if self.type == 0:
            startingState = State(BoardRepresentation=self.BoardRepresentation, turn=self.turn, function=self.function)
        else:
            startingState = State(BoardRepresentation=self.BoardRepresentation, turn=self.turn, function=self.function, height=3, width=10)
        v = MIN_LIMIT
        for action in startingState.available_actions():
            self.blocks += 1
            newState = startingState.transfer(action)
            if newState.isgoalstate():
                final_action = action
                break
            minresult = self.min_value(newState, 1)
            if minresult > v:
                final_action = action
                v = minresult
        if self.turn == 1:
            self.piece_num = startingState.transfer(final_action).white_num
        elif self.turn == 2:
            self.piece_num = startingState.transfer(final_action).black_num
        print(final_action.getString())
        return startingState.transfer(final_action), self.blocks, self.piece_num


class AlphaBetaAgent: 
    def __init__(self, BoardRepresentation, turn, depth, function, type=0):
        self.BoardRepresentation = BoardRepresentation
        self.turn = turn
        self.maxdepth = depth
        self.function = function
        self.type = type
        self.blocks = 0
        self.piece_num = 0

    def max_value(self, state, alpha, beta, depth):
        if depth == self.maxdepth or state.isgoalstate() != 0:
            return state.utility(self.turn)
        v = MIN_LIMIT
        actions = state.available_actions()
        actions = sorted(state.available_actions(), key=lambda action: 0, reverse=True)
 
        for action in actions:
            self.blocks += 1

            v = max(v, self.min_value(state.transfer(action), alpha, beta, depth + 1))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(self, state, alpha, beta, depth):
        if depth == self.maxdepth or state.isgoalstate() != 0:
            return state.utility(self.turn)
        v = MAX_LIMIT
        actions = state.available_actions()
        actions = sorted(state.available_actions(), key=lambda action: 0)

        for action in actions:
            self.blocks += 1

            v = min(v, self.max_value(state.transfer(action), alpha, beta, depth + 1))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

    
    def alpha_beta_decision(self):
        final_action = None
        if self.type == 0:
            startingState = State(BoardRepresentation=self.BoardRepresentation, turn=self.turn, function=self.function)
        else:
            startingState = State(BoardRepresentation=self.BoardRepresentation, turn=self.turn, function=self.function, height=4, width=10)
        v = MIN_LIMIT
        for action in startingState.available_actions():
            self.blocks += 1

            newState = startingState.transfer(action)
            if newState.isgoalstate():
                final_action = action
                break
            minresult = self.min_value(newState, MIN_LIMIT, MAX_LIMIT, 1)
            if minresult > v:
                final_action = action
                v = minresult
        print(v)
        if self.turn == 1:
            self.piece_num = startingState.transfer(final_action).white_num
        elif self.turn == 2:
            self.piece_num = startingState.transfer(final_action).black_num
        print(final_action.getString())
        return startingState.transfer(final_action), self.blocks, self.piece_num

class StrategicGame:

    def __init__(self):
        #Initialize all game variables and setup
        
        pygame.init()
        
        self.window_width, self.window_height = 1000, 750  # Increased from 800x600
        self.grid_size = int(700/8)  # Increased board size from 560 to 700
        self.window = pygame.display.set_mode((self.window_width, self.window_height))
        self.window.fill([255, 255, 255])
        self.game_board = 0
        self.black_piece = 0
        self.white_piece = 0
        self.reset_button = 0
        self.victory_icon = 0
        self.game_state = [[1, 1, 1, 1, 1, 1, 1, 1],
                             [1, 1, 1, 1, 1, 1, 1, 1],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [0, 0, 0, 0, 0, 0, 0, 0],
                             [2, 2, 2, 2, 2, 2, 2, 2],
                             [2, 2, 2, 2, 2, 2, 2, 2]]

        self.game_phase = 0
        self.current_player = 1
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        self.player1_explored = 0
        self.player2_explored = 0
        self.player1_duration = 0
        self.player2_duration = 0
        self.player1_turns = 0
        self.player2_turns = 0
        self.captured_count = 0

        pygame.display.set_caption("The Breakthrough Game")

        self.game_timer = pygame.time.Clock()
        self.load_resources()

    def load_resources(self):
        #loads and runs the games assets such as images
        self.game_board = pygame.image.load_extended(os.path.join('images', 'chessboard.jpg'))
        self.game_board = pygame.transform.scale(self.game_board, (700, 700))  # Increased from 560x560
        self.black_piece = pygame.image.load_extended(os.path.join('images', 'blackchess.png'))
        self.black_piece = pygame.transform.scale(self.black_piece, (self.grid_size- 20, self.grid_size - 20))
        self.white_piece = pygame.image.load_extended(os.path.join('images', 'whitechess.png'))
        self.white_piece = pygame.transform.scale(self.white_piece, (self.grid_size - 20, self.grid_size - 20))
        self.reset_button = pygame.image.load_extended(os.path.join('images', 'reset.jpg'))
        self.reset_button = pygame.transform.scale(self.reset_button, (80, 80))
        self.victory_icon = pygame.image.load_extended(os.path.join('images', 'winner.png'))
        self.victory_icon = pygame.transform.scale(self.victory_icon, (250, 250))

    def run(self):
        #runs the game
        self.game_timer.tick(90)
        self.window.fill([255, 255, 255])

        if self.game_phase in [5, 6, 7, 8, 9, 10]:
            if self.game_phase == 5:  # Minimax (Off1) vs Alpha-beta (Off1)
                if self.current_player == 1:
                    player1search = 1  # Minimax
                    player1heur = 1    # Offensive 1
                else:
                    player2search = 2  # Alpha-beta
                    player2heur = 1    # Offensive 1

            elif self.game_phase == 6:  # Alpha-beta (Off2) vs Alpha-beta (Def1)
                player1search = 2  # Alpha-beta
                player2search = 2  # Alpha-beta
                if self.current_player == 1:
                    player1heur = 3    # Offensive 2
                else:
                    player2heur = 2    # Defensive 1

            elif self.game_phase == 7:  # Alpha-beta (Def2) vs Alpha-beta (Off1)
                player1search = 2  # Alpha-beta
                player2search = 2  # Alpha-beta
                if self.current_player == 1:
                    player1heur = 4    # Defensive 2
                else:
                    player2heur = 1    # Offensive 1

            elif self.game_phase == 8:  # Alpha-beta (Off2) vs Alpha-beta (Off1)
                player1search = 2  # Alpha-beta
                player2search = 2  # Alpha-beta
                if self.current_player == 1:
                    player1heur = 3    # Offensive 2
                else:
                    player2heur = 1    # Offensive 1

            elif self.game_phase == 9:  # Alpha-beta (Def2) vs Alpha-beta (Def1)
                player1search = 2  # Alpha-beta
                player2search = 2  # Alpha-beta
                if self.current_player == 1:
                    player1heur = 4    # Defensive 2
                else:
                    player2heur = 2    # Defensive 1

            elif self.game_phase == 10:  # Alpha-beta (Off2) vs Alpha-beta (Def2)
                player1search = 2  # Alpha-beta
                player2search = 2  # Alpha-beta
                if self.current_player == 1:
                    player1heur = 3    # Offensive 2
                else:
                    player2heur = 4    # Defensive 2

            if self.current_player == 1:
                start = time.process_time()
                self.ai_move(player1search, player1heur)
                self.player1_duration += (time.process_time() - start)
                self.player1_turns += 1
                print('Total number of steps by Player 1  = ', self.player1_turns,
                      'Total number of steps covered by Player 1  = ', self.player1_explored, "\n",
                      'Average blocks covered per move by Player 1 = ', self.player1_explored / self.player1_turns,
                      'Average time taken per step by Player 1  = ', self.player1_duration / self.player1_turns, "\n",
                      'Player 1 has captured = ', self.captured_count)
            elif self.current_player == 2:
                start = time.process_time()
                self.ai_move(player2search, player2heur)
                self.player2_duration += (time.process_time() - start)
                self.player2_turns += 1
                print('Total number of steps by Player 2 = ', self.player2_turns,
                      'Total number of steps covered by Player 2 = ', self.player2_explored, "\n",
                      'Average blocks covered per move by Player 2 = ', self.player2_explored / self.player2_turns,
                      'Average time taken per step by Player 2 = ', self.player2_duration / self.player2_turns, "\n",
                      'Player 2 has captured ', self.captured_count)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  #esc to quit
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and self.isreset(event.pos):
                self.game_state = [[1, 1, 1, 1, 1, 1, 1, 1],
                                  [1, 1, 1, 1, 1, 1, 1, 1],
                                  [0, 0, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 0, 0],
                                  [0, 0, 0, 0, 0, 0, 0, 0],
                                  [2, 2, 2, 2, 2, 2, 2, 2],
                                  [2, 2, 2, 2, 2, 2, 2, 2]]
                self.current_player = 1
                self.game_phase = 0
                self.player1_explored = 0
                self.player2_explored = 0
                self.player1_duration = 0
                self.player2_duration = 0
                self.player1_turns = 0
                self.player2_turns = 0
                self.captured_count = 0

            #checks which matchup button was clicked
            # then sets the corresponding game phase
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(1, event.pos):
                self.game_phase = 5 #match 1
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(2, event.pos):
                self.game_phase = 6 #match 2
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(3, event.pos):
                self.game_phase = 7 #match 3
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(4, event.pos):
                self.game_phase = 8 #match 4
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(5, event.pos):
                self.game_phase = 9 #match 5
            elif event.type == pygame.MOUSEBUTTONDOWN and self.ismatchup(6, event.pos):
                self.game_phase = 10 # match 6

        self.display()
        pygame.display.flip()

    #Graphical User Interface part starst here
    #as clear and clean as it can be 

    def display(self): #displays the game board
        #draws the board and other elments needed to be called
        self.window.blit(self.game_board, (0, 0))
        for i in range(8):
            for j in range(8):
                if self.game_state[i][j] == 1:
                    self.window.blit(self.black_piece, (self.grid_size * j + 15, self.grid_size * i + 15))
                elif self.game_state[i][j] == 2:
                    self.window.blit(self.white_piece, (self.grid_size * j + 15, self.grid_size * i + 15))

        #draws right panel with white background
        panel_rect = pygame.Rect(720, 0, 260, self.window_height)  
        pygame.draw.rect(self.window, (240, 240, 240), panel_rect)
        
        #draws the Reset game box with border
        reset_box = pygame.Rect(735, 15, 230, 40)  
        pygame.draw.rect(self.window, (255, 255, 255), reset_box)
        pygame.draw.rect(self.window, (0, 0, 0), reset_box, 1)
        
        font = pygame.font.Font(None, 32)  # Increased font size
        text = font.render("Reset Game", True, (0, 0, 0))
        text_rect = text.get_rect(center=reset_box.center)
        self.window.blit(text, text_rect)

        #draws Current Turn text that is not in the box
        turn_label = font.render("Current Turn:", True, (0, 0, 0))
        turn_rect = turn_label.get_rect(center=(850, 80))  #
        self.window.blit(turn_label, turn_rect)
        
        turn_value = font.render("Black" if self.current_player == 1 else "White", True, (0, 0, 0))
        value_rect = turn_value.get_rect(center=(850, 110)) 
        self.window.blit(turn_value, value_rect)

        #draws the Game modes text not in the box
        modes_text = font.render("Game Modes", True, (0, 0, 0))
        modes_rect = modes_text.get_rect(center=(850, 150))  
        self.window.blit(modes_text, modes_rect)

        #Matchup descriptions 
        modes = [
            ("Match 1:", "Minimax (Off1)", "vs", "Alpha-beta (Off1)"),
            ("Match 2:", "Alpha-beta (Off2)", "vs", "Alpha-beta (Def1)"),
            ("Match 3:", "Alpha-beta (Def2)", "vs", "Alpha-beta (Off1)"),
            ("Match 4:", "Alpha-beta (Off2)", "vs", "Alpha-beta (Off1)"),
            ("Match 5:", "Alpha-beta (Def2)", "vs", "Alpha-beta (Def1)"),
            ("Match 6:", "Alpha-beta (Off2)", "vs", "Alpha-beta (Def2)")
        ]

        font_small = pygame.font.Font(None, 28)
        button_height = 80  
        spacing = 5

        for i, mode in enumerate(modes):
            button_y = 180 + (i * (button_height + spacing))  
            button_rect = pygame.Rect(735, button_y, 230, button_height)  
            
            #draws white box with black border
            pygame.draw.rect(self.window, (255, 255, 255), button_rect)
            pygame.draw.rect(self.window, (0, 0, 0), button_rect, 1)
            
            #draws the title (Match #:)
            title = font_small.render(mode[0], True, (0, 0, 0))
            title_rect = title.get_rect(center=(button_rect.centerx, button_y + 20))
            self.window.blit(title, title_rect)
            
            #draws first algorithm
            algo1 = font_small.render(mode[1], True, (0, 0, 0))
            algo1_rect = algo1.get_rect(center=(button_rect.centerx, button_y + 40))
            self.window.blit(algo1, algo1_rect)
            
            #draws the versus VS
            vs = font_small.render(mode[2], True, (0, 0, 0))
            vs_rect = vs.get_rect(center=(button_rect.centerx, button_y + 55))
            self.window.blit(vs, vs_rect)
            
            #draws second algorithm
            algo2 = font_small.render(mode[3], True, (0, 0, 0))
            algo2_rect = algo2.get_rect(center=(button_rect.centerx, button_y + 70))
            self.window.blit(algo2, algo2_rect)

        #draws the Total Time box at the bottom
        time_box = pygame.Rect(735, 690, 230, 40) 
        pygame.draw.rect(self.window, (255, 255, 255), time_box)
        pygame.draw.rect(self.window, (0, 0, 0), time_box, 1)
        
        total_time = self.player1_duration + self.player2_duration
        time_text = f"Total Time: {total_time:.1f}s"
        time_surface = font_small.render(time_text, True, (0, 0, 0))
        time_rect = time_surface.get_rect(center=time_box.center)
        self.window.blit(time_surface, time_rect)

        #draws the  victory message if game is over when won 
        if self.game_phase == 3:
            overlay = pygame.Surface((self.window_width, self.window_height))
            overlay.fill((255, 255, 255))
            overlay.set_alpha(180)
            self.window.blit(overlay, (0, 0))
            
            self.window.blit(self.victory_icon, (100, 100))
            winner = "White Pieces" if self.current_player == 1 else "Black Pieces"
            
            font_large = pygame.font.Font(None, 48)
            text = font_large.render(f"{winner} Win!", True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.window_width // 3, self.window_height // 2))
            self.window.blit(text, text_rect)

    def isreset(self, pos):
        #checks when reset or if reset button was clicked
        x, y = pos
        return 735 <= x <= 965 and 15 <= y <= 55

    def ismatchup(self, matchup, pos):
        #checks when matchup or if match button was clicked
        x, y = pos
        button_y = 180 + ((matchup - 1) * 85)
        return 735 <= x <= 965 and button_y <= y <= button_y + 80

    def ai_move(self, searchtype, evaluation):
        if searchtype == 1:
            return self.ai_move_minimax(evaluation)
        elif searchtype == 2:
            return self.ai_move_alphabeta(evaluation)

    def ai_move_minimax(self, function_type):
        board, blocks, piece = MinimaxAgent(self.game_state, self.current_player, 3, function_type).minimax_decision()
        self.game_state = board.getMatrix()
        if self.current_player == 1:
            self.player1_explored += blocks
            self.current_player = 2
        elif self.current_player == 2:
            self.player2_explored += blocks
            self.current_player = 1
        self.captured_count = 16 - piece
        if self.isgoalstate():
            self.game_phase = 3

    def ai_move_alphabeta(self, function_type):
        board, blocks, piece = AlphaBetaAgent(self.game_state, self.current_player, 4, function_type).alpha_beta_decision()
        self.game_state = board.getMatrix()
        if self.current_player == 1:
            self.player1_explored += blocks
            self.current_player = 2
        elif self.current_player == 2:
            self.player2_explored += blocks
            self.current_player = 1
        self.captured_count = 16 - piece
        if self.isgoalstate():
            self.game_phase = 3

    def isgoalstate(self, base=0):
        if base == 0:
            if 2 in self.game_state[0] or 1 in self.game_state[7]:
                return True
            else:
                for line in self.game_state:
                    if 1 in line or 2 in line:
                        return False
            return True
        else:
            count = 0
            for i in self.game_state[0]:
                if i == 2:
                    count += 1
            if count == 3:
                return True
            count = 0
            for i in self.game_state[7]:
                if i == 1:
                    count += 1
            if count == 3:
                return True
            count1 = 0
            count2 = 0
            for line in self.game_state:
                for i in line:
                    if i == 1:
                        count1 += 1
                    elif i == 2:
                        count2 += 1
            if count1 <= 2 or count2 <= 2:
                return True
        return False

def main():
    game = StrategicGame()
    while 1:
        game.run()
    while 0:
        print("La Fin")

if __name__ == '__main__':
    main()