from bshell.commands import Command

class Undo(Command):

    keywords = ['undo']
    help_text = """{keyword}
{divider}
Summary: Undo the last move played to the search board.

Usage: {keyword}
"""

    def do_command(self, *args):
        self.state.search_board.remove_last_move()

        command = self.state.commands.get('board') or None
        if not command:
            print('Command not found: board')
            return

        command.do_command()
