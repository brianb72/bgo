import os
from bshell.commands import Command


class Cwd(Command):

    keywords = ['cwd']
    help_text = """{keyword}
{divider}
Summary: Shows the current working directory.

Usage: {keyword}
"""

    def do_command(self, *args):
        print(f'   Current working directory: {self.state.working_dir}')
