"""
    bGo by BrianB (troff.troff@gmail.com)

    game_of_go.py
        The code for this file comes from:
            http://www.moderndescartes.com/essays/implementing_go/
            https://github.com/brilee/go_implementation/blob/master/go_naive.py

        Creates a Position object which represents a go board with stones on it.
        Moves can be added to the Position and a new Position object is returned.
        Position object handles the rules of go such as captures and ko.
        Raises IllegalMove if the rules of go are violated.

        TODO Rewrite for more speed.
            Consider caching moves -> positions in SQL for fast lookup of known positions?
            Instead of calling find_reached() for every move, cache groups and liberty counts, update during move.

    Old speed fix for fast duplicate game check:

    Calling Position.play_move() is expensive because of find_reached(), which scans chains of stones to count liberties
    and consider captures.

    PositionSimple() is an alternate class that accepts moves with .play_move() but does not consider the rules of Go. Stones
    are placed on the board without considering captures, ko, suicides, or even playing on top of an existing stone. This
    is useful for quickly creating a final board hash where we need to check a game for uniqueness without caring about position.

    Unique check using Position() on 1997 games
         234598577 function calls (234596228 primitive calls) in 113.418 seconds
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
  6200336   25.331    0.000   33.878    0.000 game_of_go.py:47(find_reached)
  3360112   15.345    0.000   73.923    0.000 game_of_go.py:180(play_move)
  6200336    6.497    0.000   46.105    0.000 game_of_go.py:78(maybe_capture_stones)
 65720025    5.156    0.000    5.156    0.000 {method 'add' of 'set' objects}
    13797    4.797    0.000    6.897    0.000 coords.py:35(transform_move_pair_list)

    Unique check using PositionSimple() on 1997 games
             77412460 function calls (77410111 primitive calls) in 52.788 seconds
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
     4544   19.349    0.004   19.349    0.004 {method 'commit' of 'sqlite3.Connection' objects}
    27594    9.186    0.000   13.115    0.000 coords.py:35(transform_move_pair_list)
  3360112    3.979    0.000    8.310    0.000 game_of_go.py:306(play_move)
 18480616    2.715    0.000    2.715    0.000 {method 'index' of 'str' objects}

"""


import itertools
from collections import namedtuple
import bgo.coords as coords

N = 19
NN = N ** 2
WHITE, BLACK, EMPTY = 'O', 'X', '.'

EMPTY_BOARD = EMPTY * NN


def swap_colors(color):
    if color == BLACK:
        return WHITE
    elif color == WHITE:
        return BLACK
    else:
        return color


def flatten(c):
    return N * c[0] + c[1]


# Convention: coords that have been flattened have a "f" prefix
def unflatten(fc):
    return divmod(fc, N)


def is_on_board(c):
    return c[0] % N == c[0] and c[1] % N == c[1]


def get_valid_neighbors(fc):
    x, y = unflatten(fc)
    possible_neighbors = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
    return [flatten(n) for n in possible_neighbors if is_on_board(n)]


# Neighbors are indexed by flat coordinates
NEIGHBORS = [get_valid_neighbors(fc) for fc in range(NN)]


def find_reached(board, fc):
    color = board[fc]
    chain = set([fc])
    reached = set()
    frontier = [fc]
    while frontier:
        current_fc = frontier.pop()
        chain.add(current_fc)
        for fn in NEIGHBORS[current_fc]:
            if board[fn] == color and not fn in chain:
                frontier.append(fn)
            elif board[fn] != color:
                reached.add(fn)
    return chain, reached


class IllegalMove(Exception): pass


def place_stone(color, board, fc):
    return board[:fc] + color + board[fc + 1:]


def bulk_place_stones(color, board, stones):
    byteboard = bytearray(board, encoding='ascii')  # create mutable version of board
    color = ord(color)
    for fstone in stones:
        byteboard[fstone] = color
    return byteboard.decode('ascii')  # and cast back to string when done


def maybe_capture_stones(board, fc):
    chain, reached = find_reached(board, fc)
    if not any(board[fr] == EMPTY for fr in reached):
        board = bulk_place_stones(EMPTY, board, chain)
        return board, chain
    else:
        return board, []


def play_move_incomplete(board, fc, color):
    if board[fc] != EMPTY:
        raise IllegalMove
    board = place_stone(color, board, fc)

    opp_color = swap_colors(color)
    opp_stones = []
    my_stones = []
    for fn in NEIGHBORS[fc]:
        if board[fn] == color:
            my_stones.append(fn)
        elif board[fn] == opp_color:
            opp_stones.append(fn)

    for fs in opp_stones:
        board, _ = maybe_capture_stones(board, fs)

    for fs in my_stones:
        board, _ = maybe_capture_stones(board, fs)

    return board


def is_koish(board, fc):
    'Check if fc is surrounded on all sides by 1 color, and return that color'
    if board[fc] != EMPTY: return None
    neighbor_colors = {board[fn] for fn in NEIGHBORS[fc]}
    if len(neighbor_colors) == 1 and not EMPTY in neighbor_colors:
        return list(neighbor_colors)[0]
    else:
        return None


# Raises IllegalMove
def build_position_from_move_string(move_string, rotation=0):
    return build_position_from_move_pair_list(coords.convert_move_string_to_pair_list(move_string), rotation)


# Raises IllegalMove
def build_position_from_move_pair_list(move_pair_list, rotation=0):
    p = Position.initial_state()
    color = BLACK

    if rotation == 0:
        use_move_pair_list = move_pair_list  # identity, no rotation needed
    else:
        use_move_pair_list = coords.transform_move_pair_list(move_pair_list, rotation)

    for move in use_move_pair_list:
        p = p.play_move(move, color)
        color = swap_colors(color)

    return p


# Raises IllegalMove
def build_positionsimple_from_move_pair_list(move_pair_list, rotation=0):
    p = PositionSimple.initial_state()
    color = BLACK

    if rotation == 0:
        use_move_pair_list = move_pair_list  # identity, no rotation needed
    else:
        use_move_pair_list = coords.transform_move_pair_list(move_pair_list, rotation)

    for move in use_move_pair_list:
        p = p.play_move(move, color)
        color = swap_colors(color)

    return p


# Returns the rotation needed to go from position_a to position_b, or -1 if none.
def are_move_strings_rotated_positions(move_string_a, move_string_b):
    position_a = build_position_from_move_string(move_string_a)
    position_b = build_position_from_move_string(move_string_b)

    if position_a.get_board() == position_b.get_board():
        return 0;  # Identity rotation

    for rotation_number in range(1, 8):
        position_rotated = build_position_from_move_string(coords.transform_move_string(move_string_a, rotation_number))
        if position_rotated.get_board() == position_b.get_board():
            return rotation_number  # rotation_number transforms position_a to position_b

    return -1  # Not a rotation


# board is from Position.get_board(), a 361 character string representing a go board in flat coordinates
def get_hash_for_board(board):
    hash = 0
    for i in range(361):
        if board[i] == BLACK:
            hash += const_hash_list[i]
        elif board[i] == WHITE:
            hash -= const_hash_list[i]
    return hash





class Position(namedtuple('Position', ['board', 'ko'])):
    @staticmethod
    def initial_state():
        return Position(board=EMPTY_BOARD, ko=None)

    def get_board(self):
        return self.board

    def __str__(self):
        import textwrap
        return '\n'.join(textwrap.wrap(self.board, N))

    # Flatten expects y,x
    def play_move(self, two_letter_move, color):
        board, ko = self

        # fc = flatten(('abcdefghijklmnopqrs'[::-1].index(two_letter_move[0]), 'abcdefghijklmnopqrs'[::-1].index(two_letter_move[1])))

        try:
            if two_letter_move[0] == 't' or two_letter_move[1] == 't':
                return self
            fc = flatten(
                ('abcdefghijklmnopqrs'.index(two_letter_move[1]), 'abcdefghijklmnopqrs'.index(two_letter_move[0])))
        except (IndexError, ValueError):
            raise IllegalMove("Move %s cannot be decoded." % (two_letter_move))

        if fc == ko:
            raise IllegalMove("Move at %s illegally retakes ko." % (fc))

        if board[fc] != EMPTY:
            raise IllegalMove("Stone exists at %s." % (fc))

        possible_ko_color = is_koish(board, fc)
        new_board = place_stone(color, board, fc)

        opp_color = swap_colors(color)
        opp_stones = []
        my_stones = []
        for fn in NEIGHBORS[fc]:
            if new_board[fn] == color:
                my_stones.append(fn)
            elif new_board[fn] == opp_color:
                opp_stones.append(fn)

        opp_captured_count = 0
        opp_captured_stones = []
        for fs in opp_stones:
            new_board, opp_captured = maybe_capture_stones(new_board, fs)
            opp_captured_count += len(opp_captured)
            opp_captured_stones.append(opp_captured)
        # Check for suicide
        new_board, captured = maybe_capture_stones(new_board, fc)
        if captured:
            raise IllegalMove("Move at %s is suicide." % (fc))

        if opp_captured_count == 1 and possible_ko_color == opp_color:
            # TODO this was in the original file and is wrong, changing to captured
            # new_ko = list(opp_captured)[0]
            new_ko = list(opp_captured_stones[0])
        else:
            new_ko = None

        return Position(new_board, new_ko)

    def score(self):
        board = self.board
        while EMPTY in board:
            fempty = board.index(EMPTY)
            empties, borders = find_reached(board, fempty)
            possible_border_color = board[list(borders)[0]]
            if all(board[fb] == possible_border_color for fb in borders):
                board = bulk_place_stones(possible_border_color, board, empties)
            else:
                # if an empty intersection reaches both white and black,
                # then it belongs to neither player.
                board = bulk_place_stones('?', board, empties)
        return board.count(BLACK) - board.count(WHITE)

    def get_liberties(self):
        board = self.board
        liberties = bytearray(NN)
        for color in (WHITE, BLACK):
            while color in board:
                fc = board.index(color)
                stones, borders = find_reached(board, fc)
                num_libs = len([fb for fb in borders if board[fb] == EMPTY])
                for fs in stones:
                    liberties[fs] = num_libs
                board = bulk_place_stones('?', board, stones)
        return list(liberties)


class PositionSimple(namedtuple('Position', ['board', 'ko'])):
    @staticmethod
    def initial_state():
        return PositionSimple(board=EMPTY_BOARD, ko=None)

    def get_board(self):
        return self.board

    def __str__(self):
        import textwrap
        return '\n'.join(textwrap.wrap(self.board, N))

    # Flatten expects y,x
    def play_move(self, two_letter_move, color):
        board, ko = self

        # Decode the move into an FC, ths is the only place we can raise IllegalMove()
        try:
            if two_letter_move[0] == 't' or two_letter_move[1] == 't':
                return self
            fc = flatten(
                ('abcdefghijklmnopqrs'.index(two_letter_move[1]), 'abcdefghijklmnopqrs'.index(two_letter_move[0])))
        except (IndexError, ValueError):
            raise IllegalMove("Move %s cannot be decoded." % (two_letter_move))

        # Create a new board and return it with no ko
        new_board = place_stone(color, board, fc)
        return PositionSimple(new_board, None)


const_hash_list = [840137363, 1899467765, 2245934378, 165313342, 2754462454, 714355976, 4098738971, 4006584887,
                   196740119, 3611377136, 843653099, 1996037600, 1774875911, 1232399338, 3393166909, 4201045945,
                   52866735, 2094162675, 878552623, 2089070380, 3850117764, 2579201112, 471329504, 812302803,
                   4254109070, 2029048022, 569085185, 4060716085, 1266986432, 2274386222, 1492783248, 3209458428,
                   1949324764, 2456769828, 1977848994, 1014227256, 2642085939, 307062132, 3415388841, 988538091,
                   3273147585, 3743430317, 600537047, 3380406489, 1711500608, 3157552818, 3092350566, 391748660,
                   1890177522, 477193385, 1523179465, 1351597035, 4189710241, 782954428, 4111320164, 3728297119,
                   3980547839, 2472712060, 4103641293, 503427272, 625987203, 1183506775, 4269983942, 3160364845,
                   3116473978, 1649929416, 2382921927, 3949775800, 1863296736, 969943002, 2549449385, 3934778285,
                   2195011833, 1501611713, 263746273, 2072054658, 3328780404, 2738879601, 2446800450, 1007304140,
                   1589642670, 2494836629, 3130235689, 4064689512, 3143216915, 3465950759, 225109471, 1541294964,
                   3080343664, 3979469025, 268084523, 1100963897, 2070746872, 854019704, 2007832630, 3727657436,
                   944484770, 1445263444, 2667132280, 3690349735, 2519375130, 3046352685, 4283266532, 3198357581,
                   966221126, 1858229711, 1527965324, 3640554008, 31574595, 3681442201, 4217543989, 4208942061,
                   3678233696, 456306666, 3891919084, 1151559873, 1442294628, 1337043078, 529643175, 2333295611,
                   3793387379, 2858312438, 2429354246, 950844045, 117924993, 1548378973, 357884651, 1225118331,
                   2690178984, 3280887039, 2146722464, 1979709987, 1846065177, 3714171516, 1388940337, 2202279009,
                   3467232970, 3418109369, 1952374850, 2480028007, 3439949300, 4190295264, 1120929830, 3450554474,
                   829051504, 3746354234, 333563289, 513557002, 245513684, 1950435867, 445069536, 1146030278,
                   3355246479, 2343694529, 3220254783, 2585624437, 3936327912, 3903135443, 581903740, 2929850870,
                   667315225, 250832211, 283666744, 955364564, 250785957, 4034983237, 527128695, 3684052237, 635165819,
                   2514279370, 1287316592, 362939892, 3782323368, 4127759714, 2744129706, 3772069917, 2039122922,
                   919449169, 1619479333, 2036222121, 2613266899, 484701694, 2944582305, 3847539208, 1076740327,
                   981655323, 158279866, 492179534, 2744439119, 2978489098, 123043275, 305995369, 2239354890,
                   2986121394, 3207153549, 1421063334, 4181748387, 525293306, 1412051619, 2438082137, 2798277297,
                   4226042000, 2522279626, 1083086221, 3893502738, 2969684050, 3618224076, 2316445324, 2290404771,
                   1335282882, 3375003097, 2709222189, 203377110, 2546486848, 72101321, 1395503450, 1494393937,
                   2697793240, 3796380133, 957299103, 1122246272, 821707919, 507851306, 2664964383, 318517621,
                   919851038, 3078100649, 1885270375, 2806241286, 2880012736, 3196046313, 3777992975, 736093713,
                   3969476871, 858849937, 2667627584, 340410327, 1395748688, 1787179710, 712761002, 2806649913,
                   3718345889, 3296274975, 3602477132, 2591889153, 2625959249, 3005529799, 734143650, 846059156,
                   1862271035, 3889195122, 645470575, 4090543745, 1590714529, 3509573010, 2282717546, 2848017793,
                   4042058936, 1163095716, 1573572478, 3367607511, 3316428276, 3797781956, 3899668836, 1017958226,
                   3304580302, 925741819, 2265313524, 3623035584, 3234299209, 211905457, 2033360938, 3387052464,
                   2813131977, 4275126199, 2390428690, 2448913817, 4235918277, 3003659102, 2221295353, 3185578819,
                   130827151, 1130798875, 1295212550, 1459832842, 1212994052, 2587468123, 2550244401, 2552674340,
                   3292510399, 1950968062, 4075242543, 4049515720, 1767784450, 2262480629, 4199221080, 1169953213,
                   1329447506, 1891077717, 3080223072, 1608817972, 3503123381, 2773926677, 4008188500, 515007460,
                   413638182, 2036360478, 1767032659, 750106383, 4049724396, 2746781618, 449109822, 1535981776,
                   640991578, 2029372003, 1170266051, 3825523928, 993535183, 140496877, 2788027137, 2121906844,
                   124610112, 659113631, 1118383171, 471342623, 1474534794, 2480038934, 2967454551, 2919170399,
                   3778596972, 3420076345, 2459283397, 1983587618, 4048912334, 4084398645, 2848258829, 2648940108,
                   3800514225, 381362292, 1669024592, 3188657598, 1659798847, 2157936957, 1326768500, 3752653896,
                   2725919425, 1128318170, 215383668, 3844272023, 3775815883, 2067084053, 1214945249, 1371360989,
                   2132683990, 1217601152, 1525159386, 4227669814, 2660244675, 3030184365, 1914212585, 1564074740]

