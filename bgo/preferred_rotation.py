"""
bGo by BrianB (troff.troff@gmail.com)

TODO
    Not working right in a few situations, need a rethink and rewrite of logic
    Make me better

preferred.py
    Given any moves or position, the board can be rotated and mirrored in 8 different ways.
    When producing diagrams the board should be rotated so that the first move is always in the upper left,
    the second move is always in the lower left or upper left, etc.
    This class will follow rules defining where we want stones, and return the rotation that best follows those rules.




Each move that is placed on the board can be placed in either
    Upper Left, Upper Right, Lower Left, Lower Right

The J line is the midpoint line.
If X (horizontal) is J then the move can be Upper or Lower
If Y (vertical) is J then the move can be Left or Right

JJ is the center point and should be considered a pass.


CODE
----------------

L = upper left
l = lower left

R = upper right
r = lower right

H = horizontal upper  (top half of board)
h = horizontal lower (lower half of board)

V = vertical upper (right half of board)
v = vertical lower (left half of board)


These codes are used to encode the move_pair_list and produce a string like this:
    RlrL  would be upper right, lower left, lower right, lower left

The first letter is the X (horizontal) coordinate
The second letter is the Y (vertical) coordinate

'PD' is the upper right star point
"""


# Larger is more preferred, smaller is less
# Returns -1 if a < b   0 if a = b   1 if a > b
def compare_opening_strings(a, b):
    # Less prefered to More Prefered

    strength_black = 'vVhHLlrR'
    strength_white = 'VvHhRrLl'

    min_len = min(len(a), len(b))

    for i in range(min_len):
        if i % 2: # white
            if strength_white.index(a[i]) < strength_white.index(b[i]):
                return -1
            elif strength_white.index(a[i]) > strength_white.index(b[i]):
                return 1
        else: # black
            if strength_black.index(a[i]) < strength_black.index(b[i]):
                return -1
            elif strength_black.index(a[i]) > strength_black.index(b[i]):
                return 1

    return 0



def pick_preferred_rotation(rotated_move_pair_lists):
    opening_string_list = [convert_move_pair_list_to_opening_string(rotated_move_pair_lists[rotation][:10]) for rotation in range(8)]

    largest = 0
    for i in range(1,8):
        if compare_opening_strings(opening_string_list[i], opening_string_list[largest]) == 1:
            largest = i

    # The largest opening string in the list is our preferred rotation, 0 is identity
    return largest


# Convert a move pair list to an 'vVhHlLrR' style opening string
def convert_move_pair_list_to_opening_string(move_pair_list):
    ret = ''
    for x, y in move_pair_list:
        if x == 'j' and y =='j':
            continue    # ignore center point, omit it from return string
        elif x == 'j':
            if y < 'j':
                ret += 'H'
            else:
                ret += 'h'
        elif y == 'j':
            if x < 'j':
                ret += 'v'
            else:
                ret += 'V'
        elif x < 'j':
            if y < 'j':
                ret += 'L'
            else:
                ret += 'l'
        elif x > 'j':
            if y < 'j':
                ret += 'R'
            else:
                ret += 'r'
        else:
            raise ValueError('NEVER HIT ME')

    return ret