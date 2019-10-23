'''
bGo by BrianB (troff.troff@gmail.com)

coords.py
    Manage, translate, and rotate coordinate systems


    Coordinates
        Normal
            Two characters using letters 'a' to 's'
            First character is X coordinate (left to right)
            Top character is Y coordinate (top to bottom)
            Upper left corner of board is 'aa'
            'tt' is a pass
            '' or ' ' are nonstandard passes treat them as 'tt', some files use this
        Integer
            X,Y
                Characters are converted to a 0 based integer pair, [12, 5]
                Upper left corner of board is [0, 0]
            Flat
                Coordinates are converted to flat index between 0 and 360
                Used to access a list representing the board
            Zero Based
                X,Y coordinates are subtracted by 9 so that the upper left is [-9, -9]
                Used for rotations

    Types of Moves
        move_string         A series of moves in a single string 'DDDPQQCD'
        move_pair_list      A list of move coordinate pairs ['DD', 'DP', 'QQ', 'CD]

    Rotations
        Any go position can be rotated and/or flipped to produce 8 different rotated boards.
        Positions must be compared to see if they are rotations of another and thus the same game.

    Moves vs Position
        A position can be reached by more than one move string.
        Moves can be played in a different order and produce the same position.
        There are two types of equality between go games
            Move Equality
                The moves or rotated moves are the same
            Position Equality
                The positions or rotated positions are the same
        Generally Position is more important than Moves
'''


'''
    String names of each transformation
'''
TRANSFORMATION_NAMES = [
    'identity',
    'rotate 270 ccw',
    'rotate 180 ccw',
    'rotate 90 ccw',
    'rotate 90 and flip vertical',
    'flip horizontal',
    'rotate 270 and flip horizontal',
    'flip vertical'
]

'''
    List of transform matrixes to convert to each of the 8 rotations
'''
coord_transformations = [
            [[ 1, 0], [ 0, 1]], # 0 a - identity transformation matrix
            [[ 0,-1], [ 1, 0]], # 3 f - rotate 270 counter-clockwise
            [[-1, 0], [ 0,-1]], # 2 d - Rotate 180
            [[ 0, 1], [-1, 0]], # 1 g - Rotate 90 counter-clockwise
            [[ 0,-1], [-1, 0]], # 4 h - rotate 90 and invert
            [[-1, 0], [ 0, 1]], # 5 b - flip left
            [[ 0, 1], [ 1, 0]], # 6 e -rotate 270 and flip left
            [[ 1, 0], [ 0,-1]]  # 7 c - flip top bottom
]


'''
    Convert a move pair list ['DD', 'DP', 'QQ'] to a string 'DDDPQQ'
'''
def convert_move_pair_list_to_string(move_pair_list):
    return ''.join(move_pair_list)

'''
    Convert a move string 'DDDPQQ' to a move pair list ['DD', 'DP', 'QQ']
'''
def convert_move_string_to_pair_list(move_string):
    return [move_string[i:i + 2] for i in range(0, len(move_string), 2)]


'''
    Given two move strings A and B, test if A is a rotation of B
    Return the rotation number needed to transform move string A to move string B
    If the strings are equal return 0 for the identity transform
    If the strings are not rotations return -1
    Do not consider position, only moves. 
'''
def are_move_pair_strings_rotations(move_string_a, move_string_b):
    if move_string_a == move_string_b:
        return 0
    mpl_a = convert_move_string_to_pair_list(move_string_a)
    mpl_b = convert_move_string_to_pair_list(move_string_b)

    for i in range(1,8):
        if transform_move_pair_list(mpl_a, i) == mpl_b:
            return i
    return -1

'''
    Given two move pair lists A and B, test if A is a rotation of B
    Return the rotation number needed to transform moves A to moves B
    If the strings are equal return 0 for the identity transform
    If the strings are not rotations return -1
    Do not consider position, only moves.
'''
def are_move_pair_lists_rotations(mpl_a, mpl_b):
    if mpl_a == mpl_b:
        return 0

    for i in range(1,8):
        if transform_move_pair_list(mpl_a, i) == mpl_b:
            return i
    return -1

'''
    Transforms move_pair_list to the given rotation number
    Returns rotated moves.
    Raises ValueError if charx or chary out of range.
'''
def transform_move_pair_list(move_pair_list, rotation):
    rotated_moves = []
    for charx, chary in move_pair_list:
        # 'tt' is a pass and is not rotated
        if charx == 't' or chary == 't':
            rotated_moves.append('tt')
            continue

        # Convert to numeric coordinates and zero center
        x = ('abcdefghijklmnopqrs'.index(charx)) - 9
        y = ('abcdefghijklmnopqrs'.index(chary)) - 9


        # Rotate zero based coords
        tx = coord_transformations[rotation][0][0] * x + coord_transformations[rotation][0][1] * y
        ty = coord_transformations[rotation][1][0] * x + coord_transformations[rotation][1][1] * y

        # Convert back to move_pair
        rot_charx = chr(tx + 9 + ord('a'))
        rot_chary = chr(ty + 9 + ord('a'))
        rotated_moves.append(rot_charx + rot_chary)

    return rotated_moves

'''
    Transforms move_string to the given rotation number
    Returns rotated moves.
    Raises ValueError if charx or chary out of range.
'''
def transform_move_string(move_string, rotation):
    move_pair_list = convert_move_string_to_pair_list(move_string)
    return transform_move_pair_list(move_pair_list, rotation)

def is_valid_move(move):
    if not isinstance(move, str):
        return False
    if len(move) is not 2:
        return False
    x, y = [x.lower() in 'abcdefghijklmnopqrs' for x in tuple(move)]
    return x and y
