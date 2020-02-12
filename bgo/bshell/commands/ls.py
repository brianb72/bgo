import os
from bshell.commands import Command

class Ls(Command):

    keywords = ['ls']
    help_text = """{keyword}
{divider}
Summary: Lists the contents of the current working directory, or the specified path.

Usage: {keyword} [<path>]

Examples:

    {keyword}
    {keyword} /home/user/sgf
"""

    def do_command(self, *args):
        if not args:
            use_dir = self.state.working_dir
        else:
            use_dir = args[0]

        if not os.path.isdir(use_dir):
            print(f'Directory {use_dir} not found.')
            return

        print(f'Directory: {self.state.working_dir}')
        dirs = []
        files = []
        for item in os.listdir(self.state.working_dir):
            item_full_path = os.path.join(self.state.working_dir, item)
            if os.path.isdir(item_full_path):
                dirs.append(f'[{item}]')
            elif os.path.isfile(item_full_path):
                files.append(item)
            else:
                print(f'Unknown {item_full_path}')

        if not dirs and not files:
            print(f'   <empty>')
        else:
            if dirs:
                print(f'   Directories: {", ".join(dirs)}')
            if files:
                print(f'         Files: {", ".join(files)}')

