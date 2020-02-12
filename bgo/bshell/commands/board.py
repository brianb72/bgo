from bshell.commands import Command

class Board(Command):

    keywords = ['board']
    help_text = """{keyword}
{divider}
Summary: Shows the current play board, or resets it.

Usage: {keyword} [reset]

Examples:

    {keyword}
    {keyword} reset
"""

    def do_command(self, *args):
        if len(args) == 1 and args[0] == 'reset':
            print('   Resetting search.')
            self.state.search_board.reset()
            return

        board = self.state.search_board.get_board_as_string(show_marks=True)
        print(board)
