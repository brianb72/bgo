import os
from datetime import datetime

from bshell.commands import Command
import utils.sgf_parser as sgf_parser

from database import DBAccess, DBAccessLookupNotFound, DBAccessGameRecordError, DBAccessException, DBAccessDuplicate
import game_of_go.game_of_go as game_of_go


class Import(Command):

    keywords = ['import']
    help_text = """{keyword}
{divider}
Summary: Imports a tgz of SGF files into the current database.

Usage: {keyword} <file>

Examples:

    {keyword} game-collection.tgz
"""

    def do_command(self, *args):
        if not args and len(args) != 1:
            print(f'Needs a file to import.')
            return

        arg_path = args[0]

        if os.path.isabs(arg_path):
            import_path = arg_path
        else:
            import_path = os.path.join(self.state.working_dir, arg_path)
        if not os.path.isfile(import_path):
            print(f'Could not find file {import_path}')
            return

        _, ext = os.path.splitext(import_path)
        if ext.lower() != '.tgz':
           print(f'Target file must be a tgz.')
           return

        print(f'\n\n*** Using database file {self.state.database_path}')
        print(f'*** About to import {import_path}')
        try:
            user_input = self.state.session.prompt("   Are you sure? (YES) > ",
                key_bindings=self.state.key_bindings)
            if not user_input or user_input != 'YES':
                print(f'\nAborted.')
                return
            else:
                user_input = user_input.split()
        except (EOFError, KeyboardInterrupt):
            raise

        start_time = datetime.now()

        try:
           sgf_count, sgf_added, sgf_duplicate, sgf_parse_error, sgf_failed = self.state.db_access.add_games_from_tgz(import_path)
        except DBAccessException as e:
           print(f'Error while adding games - [{e}]')
           return

        try:
           self.state.db_access.rebuild_final_positions()
        except DBAccessException as e:
           print(f'Error while rebuilding final positions - [{e}]')
           return

        try:
           self.state.db_access.rebuild_board_hashes()
        except DBAccessException as e:
           print(f'Error while rebuilding hashes - [{e}]')
           return

        print(f'\nDone!')

        stop_time = datetime.now()
        print(f'Elapsed Time: {stop_time - start_time}')
        print(f'Found {sgf_count} game records, added {sgf_added} games.')
        print(f'{sgf_duplicate} duplicates, {sgf_parse_error} parse errors')
