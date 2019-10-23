from bshell.commands import Command
from bgo.go_board import GoBoard

class Play(Command):

    keywords = ['play']
    help_text = """{keyword}
{divider}
Summary: Plays one or more moves on the search board.
         Play a mark 'a-z'.

Usage: {keyword} [reset]

Examples:

    {keyword} <move> [<move> ...]
    {keyword} <mark letter>
    {keyword} pd
    {keyword} pd dp dd
    {keyword} a
"""

    def do_command(self, *args):
        search = self.state.search_board

        if len(args) == 0:
            print('Need move(s) or mark.')
            return

        if len(args) == 1 and len(args[0]) == 1:
            # Single character argument is playing a mark
            mark = args[0].lower()
            if mark <= 'a' and mark >= 'z':
                print('Mark must be between "a" and "z"')
                return
            move = self.state.search_board.get_move_for_mark(mark)
            if move == None:
                print(f'Mark {mark} not found.')
                return
            self.state.search_board.play(move)
        else:
            # One or more 2 character arguments are playing moves
            for move in args:
                if not search.play(move):
                    break

        # If we fell through, update the board
        command = self.state.commands.get('board') or None
        if not command:
            print('Command not found: board')
            return

        command.do_command()
