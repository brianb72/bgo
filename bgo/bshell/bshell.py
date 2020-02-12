'''
bGo by BrianB (troff.troff@gmail.com)

    bshell.py
        Provide a command line interface to:
            Maintain the database
                Reset DB
                Import new SGF
                Calculate hashes and position caches
            Perform Lookups
                Play position on text based board
                Perform lookup on moves or position
                Search database for players, games, events
                Search Joseki and Fuseki

        Uses prompt toolkit and commands patterns from:
            https://github.com/mpirnat/dndme
'''

from importlib import import_module
import os
import pkgutil
import sys
import traceback

import click
from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from bshell.models import ShellState
from database import DBAccess, DBAccessDuplicate, DBAccessException, DBAccessGameRecordError, DBAccessLookupNotFound
import game_of_go.game_of_go as game_of_go
import utils.go_board as go_board


default_sqlfile = 'database.sqlite'




def load_commands(state, session):
    path = os.path.join(os.path.dirname(__file__), "commands")
    modules = pkgutil.iter_modules(path=[path])

    for loader, mod_name, ispkg in modules:
        # Ensure that module isn't already loaded
        if mod_name not in sys.modules:

            # Import module
            loaded_mod = import_module('bshell.commands.'+mod_name)

            # Load class from imported module
            class_name = ''.join([x.title() for x in mod_name.split('_')])
            loaded_class = getattr(loaded_mod, class_name, None)
            if not loaded_class:
                continue

            # Create an instance of the class
            instance = loaded_class(state, session)

@click.command()
@click.option('--database', default=default_sqlfile,
        help=f'Database file to use; default [{default_sqlfile}]')
def main_loop(database):

    session = PromptSession()
    kb = KeyBindings()

    start_dir = os.path.dirname(os.path.realpath(__file__))
    working_dir = os.getcwd()
    database_path = os.path.join(working_dir, database)
    print(f'Start {start_dir}  Work {working_dir}')

    db_access = DBAccess(database_path)



    game_count = db_access.get_number_of_games_in_database()

    print(f'Using database [{database_path}] with {game_count} games.')


    state = ShellState(database_path=database_path,
                       working_dir=working_dir,
                       db_access=db_access,
                       session=session,
                       key_bindings=kb
                       )

    load_commands(state, session)

    while True:
        try:
            user_input = session.prompt("> ",
                key_bindings=kb)
            if not user_input:
                continue
            else:
                user_input = user_input.split()

            if user_input[0] == 'exit':
                break

            command = state.commands.get(user_input[0]) or None
            if not command:
                print("Unknown command.")
                continue

            command.do_command(*user_input[1:])

        except (EOFError, KeyboardInterrupt):
            pass
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    main_loop()