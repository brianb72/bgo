'''
    bGo by BrianB (troff.troff@gmail.com)

    go_board.py
        Wrap game_of_go and provide a class to access a single game and board.
        TODO: move game_of_go into this wrapper and do a rewrite.
'''

import game_of_go.game_of_go as game_of_go
from enum import Enum


class Color(Enum):
    Empty = 0
    Black = 1
    White = 2

# TODO check if these tuples are (x, y) or (y, x)

'''
    move is 'dp'
'''
def flatten_move(move):
    return flatten(tuple(['abcdefghijklmnopqrs'.index(x) for x in move.lower()]))

'''
    Converts X,Y coordinate to a flat coordinate between 0 and 360
    c is a tuple (x, y)
'''
def flatten(c):
    return 19 * c[0] + c[1]

'''
    Converts a flat coordinate to an (x, y) tuple
'''
def unflatten(fc):
    return divmod(fc, 19)


class GoBoard(object):

    def __init__(self):
        self.reset()


    '''
        Reset state to initial, empty board.
    '''
    def reset(self):
        self.position = game_of_go.Position.initial_state()
        self.moves = []
        self.marks = {}

    '''
        Removes the last move and rebuilds the position.
    '''
    def remove_last_move(self):
        if len(self.moves) is 0:
            self.reset()
        else:
            old_moves = self.moves
            old_moves.pop()
            self.reset()
            for move in old_moves:
                self.play(move)

    def add_mark(self, move, mark):
        self.marks[move] = mark

    def remove_mark(self, move):
        self.marks.pop(move)

    def reset_marks(self):
        self.marks = {}

    '''
        Returns move of the given mark, or None if mark does not exist.
    '''
    def get_move_for_mark(self, mark):
        inverse_mark = {v: k for k,v in self.marks.items()}
        try:
            move = inverse_mark[mark]
        except KeyError:
            return None
        return move

    def get_moves(self):
        return self.moves
    '''
        Returns the Color of the next move to be played
    '''
    def next_to_move(self):
        if (len(self.moves) + 2) % 2:
            return Color.White
        return Color.Black

    '''
        Returns the inverse of color. Empty returns empty.
    '''
    def invert_color(self, color):
        if color == Color.Empty:
            return Color.Empty
        if color == Color.Black:
            return Color.White
        if color == Color.White:
            return Color.Black
        raise ValueError(f'go_board::invert_color: Unknown color {color}')

    '''
        Plays a move on the board. 
        If any moves are invalid, play up to the invalid move and stop.
        Return True if no invalid moves, False if invalid move
    '''
    def play(self, move):
        self.reset_marks()
        color = self.next_to_move()
        if color == Color.Black:
            uc = game_of_go.BLACK
        elif color == Color.White:
            uc = game_of_go.WHITE
        else:
            print(f'   go_board:play() - Color is not Black / White')
            return

        try:
            new_position = self.position.play_move(move, uc)
        except game_of_go.IllegalMove:
            print(f"   Illegal Move '{move}'")
            return False
        self.position = new_position
        self.moves.append(move)
        color = self.invert_color(color)
        return True

    def get_board(self):
        return self.position.get_board()

    def get_board_as_list(self):
        return [list(self.position.get_board()[y * 19:y * 19 + 19]) for y in range(19)]

    def get_board_as_string(self, show_marks=False):
        hoshi_coord = [3, 9, 15]
        ret = []
        bl = self.get_board_as_list()

        if show_marks:
            # Draw the markboard onto the boardlist
            for move, mark in self.marks.items():
                x, y = ['abcdefghijklmnopqrs'.index(x) for x in tuple(move)]
                if bl[y][x] is game_of_go.EMPTY:
                    bl[y][x] = mark


        ret.append('   A B C D E F G H I J K L M N O P Q R S')
        for y in range(19):
            letter = 'ABCDEFGHIJKLMNOPQRS'[y].lower()
            if y in hoshi_coord:
                for x in hoshi_coord:
                    if bl[y][x] == game_of_go.EMPTY:
                        bl[y][x] = '+'
            row = ' '.join(bl[y])
            ret.append(f' {letter} {row} {letter}')
        ret.append('   A B C D E F G H I J K L M N O P Q R S')

        return '\n'.join(ret)
