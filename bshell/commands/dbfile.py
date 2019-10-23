import os

from bshell.commands import Command
from bgo.db_access import DBAccess, DBAccessGameRecordError, DBAccessLookupNotFound, DBAccessException, DBAccessDuplicate

class Dbfile(Command):

    keywords = ['dbfile']
    help_text = """{keyword}
{divider}
Summary: Shows the current database
         Opens a new or existing database in the current work directory

Usage: {keyword} [<filename>]

Examples:

    {keyword}
    {keyword} my_database.sql
"""

    def do_command(self, *args):
        if not args:
            print(f'   Current database: {self.state.database_path}')
            return

        input_path = args[0]
        if (os.path.isabs(input_path)):
            database_path = os.path.abspath(input_path)
        else:
            database_path = os.path.join(self.state.working_dir, input_path)

        path_dir = os.path.dirname(database_path)
        if not os.path.isdir(path_dir):
            print(f' Cannot find directory {path_dir}!')
            return

        if not os.path.lexists(database_path):
            print(f'\n\n*** Database {database_path} does not exist.')
            try:
                user_input = self.state.session.prompt("   Create new database? (YES) > ",
                                                       key_bindings=self.state.key_bindings)
                if not user_input or user_input != 'YES':
                    print(f'\nAborted.')
                    return
                else:
                    user_input = user_input.split()
            except (EOFError, KeyboardInterrupt):
                raise

        try:
            self.state.db_access = DBAccess(database_path)
        except DBAccessException as e:
            print(f'Error opening {database_path} : {e}')
            self.state.db_access = None
            return

        self.state.database_path = database_path

        try:
            game_count = self.state.db_access.get_game_count()
        except DBAccessException as e:
            print(f'Error getting game count from database {database_path} - {e}')
            self.state.db_access = None
            return

        print(f'   Opened {self.state.database_path} with {game_count} games.')
