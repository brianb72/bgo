from bshell.commands import Command
import bgo.game_of_go as game_of_go
from bgo.db_access import DBAccess, DBAccessException, DBAccessLookupNotFound, DBAccessGameRecordError

class Search(Command):

    keywords = ['search']
    help_text = """{keyword}
{divider}
Summary: Searches the database for the pattern on the current play board.

Usage: {keyword}
"""

    def do_command(self, *args):
        # Get the next move data
        db = self.state.db_access
        move_list = self.state.search_board.get_moves()

        try:
            next_move_dict = db.get_next_move_data_for_move_pair_list(move_list, all_rotations=True)
        except DBAccessException as e:
            print(f'Error while accessing database! {self.state.database_path} - {e}')
            return
        except DBAccessLookupNotFound:
            print(f'No results found')
            self.state.search_board.reset_marks()
            return

        sorted_keys = sorted(next_move_dict, key=lambda k: len(next_move_dict[k]), reverse=True)

        self.state.search_board.reset_marks()
        letter = 'abcdefghijklmnopqrstuvwxyz'
        output = []
        i = 0
        for k in sorted_keys[:6]:
            self.state.search_board.add_mark(k, letter[i])
            output.append(f'{letter[i]}: {len(next_move_dict[k])}')
            i += 1

        # Display the board
        command = self.state.commands.get('board') or None
        if not command:
            print('Command not found: board')
            return

        command.do_command()

        print(', '.join(output))
