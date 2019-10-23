from bshell.commands import Command
import bgo.game_of_go as game_of_go
from datetime import datetime


class Buildhash(Command):

    keywords = ['buildhash']
    help_text = """{keyword}
{divider}
Summary: Rebuilds the hashes for the current database.

Usage: {keyword} 
"""

    def do_command(self, *args):
        print(f'\n\n*** Really erase and rebuild all hashes? This will take some time.')
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

        db = self.state.db_access

        db.clear_all_hashes()

        game_list = db.get_all_game_id()

        count = 0
        rejected_id = []
        to_add = []

        start_total = datetime.now()
        last_update = datetime.now()

        for game_id in game_list:
            count += 1
            if count % 5000 == 0:
                tnow = datetime.now()
                print(f'   {count} / {len(game_list)} ({(count / len(game_list)) * 100:5.2f}%) [{len(to_add)} hashes buffered] [{tnow - last_update}]')
                last_update = tnow

            move_pair_list = db.get_move_list_for_game(game_id)[:30]
            move_number = 0  # starts with move 1, there is no move 0
            try:
                game = game_of_go.Position.initial_state()
                color = game_of_go.BLACK
                for i in range(len(move_pair_list)):
                    move_number = i + 1
                    try:
                        next_move = move_pair_list[i + 1]
                    except IndexError:
                        next_move = 'tt'
                    game = game.play_move(move_pair_list[i], color)
                    board_hash = game_of_go.get_hash_for_board(game.get_board())
                    to_add.append((board_hash, game_id, move_number, next_move))
                    color = game_of_go.swap_colors(color)
            except game_of_go.IllegalMove as e:
                # print("Rejecting game [%i] for [%s]" % (game_id, e))
                rejected_id.append(game_id)
                continue

            if len(to_add) > 500000:
                print(f'   ...Inserting {len(to_add)} hashes into the database.')
                start_hash = datetime.now()
                db.add_new_hash(to_add)
                to_add = []
                stop_hash = datetime.now()
                print(f'   ...Finished in {stop_hash - start_hash}')

        # One more add to flush out the remaining buffer
        if len(to_add) > 0:
            db.add_new_hash(to_add)
            to_add = []

        stop_total = datetime.now()

        print(f'Elapsed: {stop_total - start_total}')
        print(f'{len(game_list)} games processed, {len(rejected_id)} games with illegal moves.')
