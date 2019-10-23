from bshell.commands import Command
from bgo.go_board import GoBoard
import bgo.coords as coords

class Mark(Command):

    keywords = ['mark']
    help_text = """{keyword}
{divider}
Summary: Places a mark on the board, or clears the marks.

Usage: {keyword} clear
Usage: {keyword} <move> <mark>

Examples:

    {keyword} cn A
    {keyword} jd *
"""

    def do_command(self, *args):
        search = self.state.search_board

        if len(args) is 0:
            print('Need one or more moves.')
            return

        if len(args) is 1 and args[0] == 'clear':
            print('Clearing marks from board.')
            self.state.search_board.reset_marks()
        elif len(args) is 2:
            move = args[0].lower()
            mark = args[1]
            if not coords.is_valid_move(move):
                print(f'Invalid Move: {move}')
                return
            self.state.search_board.add_mark(move, mark)
        else:
            print('Need a move and a mark.')
            return

        # Run the board command
        command = self.state.commands.get('board') or None
        if not command:
            print('Command not found: board')
            return

        command.do_command()
