from bshell.commands import Command
import game_of_go.game_of_go as game_of_go
from database import DBAccess, DBAccessException, DBAccessLookupNotFound, DBAccessGameRecordError

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
            next_move_counter = db.get_next_move_counter_for_moves(move_list)
        except DBAccessException as e:
            print(f'Error while accessing database! {self.state.database_path} - {e}')
            return
        except DBAccessLookupNotFound:
            print(f'No results found')
            self.state.search_board.reset_marks()
            return

        self.state.search_board.reset_marks()
        letter = 'abcdefghijklmnopqrstuvwxyz'
        output = []
        i = 0

        for move, count in next_move_counter.most_common(6):
            self.state.search_board.add_mark(move, letter[i])
            output.append(f'{letter[i]}: {count}')
            i += 1

        # Display the board
        command = self.state.commands.get('board') or None
        if not command:
            print('Command not found: board')
            return

        command.do_command()

        print(', '.join(output))


