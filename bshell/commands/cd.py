import os
from bshell.commands import Command

class Cd(Command):

    keywords = ['cd']
    help_text = """{keyword}
{divider}
Summary: Changes the current working directory relative to the current path.

Usage: {keyword} <path>

Examples:

    {keyword} sgf
    {keyword} /home/user/sgf
"""

    def do_command(self, *args):
        if not args and len(args) is not 1:
            print(f'Needs a target.')
            return

        path = args[0]

        if os.path.isabs(path):
            path = os.path.abspath(path)
        else:
            path = os.path.join(self.state.working_dir, path)

        if not os.path.isdir(path):
            print(f'Invalid Path: {path}')
            return

        self.state.working_dir = path
        print(f'Working directory changed to {path}')