'''
bGo by BrianB (troff.troff@gmail.com)

diagrams.py
    Turns moves into a string representing a board with move numbers or next move marks. This string can be placed
    in an HTML <DIV> and parsed by the JGO javascript to produce an image of the board.

    Contains HTML strings that are used to open the document, close the document, and produce the DIVs needed to hold
    the board.
'''

import bgo.game_of_go as game_of_go

string_document_open = '''
<!DOCTYPE HTML>
<html lang="en">
<head>
    <meta charset="utf-8">tools
    <title>Board</title>
</head>
<body>
'''

# Must pass a <style></style> string in or an empty string ""
string_document_open_with_style = '''
<!DOCTYPE HTML>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Board</title>
    %s
</head>
<body>
'''

string_document_close = '''
<script type="text/javascript" src="dist/jgoboard-latest.js"></script>
<script type="text/javascript" src="small/board.js"></script>
<!-- This needs to happen after all divs are loaded, so put it below the divs -->
<script type="text/javascript">JGO.auto.init(document, JGO);</script>

</body>
</html>
'''

string_div_open_small_noblurb = '<div class="jgoboard%s" data-jgostyle="JGO.BOARD.smallBW">'
string_div_open_small_blurb = '<div class="jgoboard%s" data-game-blurb="%s" data-jgostyle="JGO.BOARD.smallBW">'

string_div_open_medium_noblurb = '<div class="jgoboard%s" data-jgostyle="JGO.BOARD.mediumBW">'
string_div_open_medium_blurb = '<div class="jgoboard%s" data-game-blurb="%s" data-jgostyle="JGO.BOARD.mediumBW">'
string_div_close = '</div>'

'''
    Returns a JGO board string that contains stones, and marks like letters or numbers.
    moves_mark_dict = {'dd': 'A'} will mark the upper left 4-4 point with the letter 'A'
    Raises: ValueError, game_of_go.IllegalMove
'''
def make_diagram_with_mark_board(move_pair_list, move_mark_dict):
    board = game_of_go.build_position_from_move_pair_list(move_pair_list).get_board()

    # Build the mark board
    mark_board = [''] * 361
    try:
        for move, mark in move_mark_dict.items():
            fc = game_of_go.flatten(('abcdefghijklmnopqrs'.index(move[1]), 'abcdefghijklmnopqrs'.index(move[0])))
            mark_board[fc] = mark
    except IndexError:
        raise ValueError()  # Reraise as ValueError

    # Generate the output board
    ret_string = ''
    for fc in range(361):
        ret_string += board[fc]
        if mark_board[fc] != '':
            ret_string += '%.2s' % (mark_board[fc],)
        else:
            ret_string += '  '
        if (fc + 1) % 19 == 0:
            ret_string += '\n'

    return ret_string


'''
    Returns a JGO board string that contains stones, with each stone marked with it's integer move number.
    Raises: game_of_go.IllegalMove
'''
def make_diagram_with_move_numbers(move_pair_list):
    board = game_of_go.build_position_from_move_pair_list(move_pair_list).get_board()

    # Build the move board
    move_board = [0 for x in range(361)]
    num = 1
    for move in move_pair_list:
        fc = game_of_go.flatten(('abcdefghijklmnopqrs'.index(move[1]), 'abcdefghijklmnopqrs'.index(move[0])))
        move_board[fc] = num
        num += 1

    # Build the output board
    ret_string = ''
    for fc in range(361):
        ret_string += board[fc]
        if move_board[fc] != 0:
            ret_string += '%2i' % (move_board[fc],)
        else:
            ret_string += '  '
        if (fc + 1) % 19 == 0:
            ret_string += '\n'

    return ret_string


