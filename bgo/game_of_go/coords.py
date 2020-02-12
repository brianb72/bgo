

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


def transform_move_pair(move_pair, rotation):
    charx, chary = move_pair.lower()
    if charx == 't' or chary == 't' or charx == ' ' or chary == ' ':
        return 'tt'
    # Convert to numeric coordinates and zero center
    x = ('abcdefghijklmnopqrs'.index(charx)) - 9
    y = ('abcdefghijklmnopqrs'.index(chary)) - 9

    # Rotate zero based coords
    tx = coord_transformations[rotation][0][0] * x + coord_transformations[rotation][0][1] * y
    ty = coord_transformations[rotation][1][0] * x + coord_transformations[rotation][1][1] * y

    # Convert back to move_pair
    rot_charx = chr(tx + 9 + ord('a'))
    rot_chary = chr(ty + 9 + ord('a'))

    return rot_charx + rot_chary

'''
    Transforms move_pair_list to the given rotation number
    Returns rotated moves.
    Raises ValueError if charx or chary out of range.
'''
def transform_move_pair_list(move_pair_list, rotation):
    if rotation == 0:
        return move_pair_list
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
    if len(move) != 2:
        return False
    try:
        x, y = [m.lower() in 'abcdefghijklmnopqrs' for m in tuple(move)]
    except AttributeError:
        return False

    return x and y
