import sqlite3
from database import DBAccessException, DBAccessDuplicate, DBAccessGameRecordError, DBAccessLookupNotFound
from game_of_go import game_of_go, coords




def clear_final_positions(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        cursor.execute('DELETE FROM final_board_hash')
        db.commit()
    except sqlite3.Error as e:
        raise DBAccessException(f'error clearing final positions - [{e}]')

def clear_board_hashes(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        cursor.execute('DELETE FROM hash_list')
        db.commit()
    except sqlite3.Error as e:
        raise DBAccessException(f'error clearing board hashes - [{e}]')

def rebuild_final_positions(self):
    print('Rebuilding final positions...')

    self.clear_final_positions()
    game_ids = self.get_all_game_id()

    count = 0
    for game_id in game_ids:
        count += 1
        if count % self.DISPLAY_MESSAGE_COUNT == 0:
            print(f'   ...{count} / {len(game_ids)}')
        moves = self.get_moves_for_game_id(game_id)
        position = game_of_go.build_positionsimple_from_move_pair_list(moves)
        hash = game_of_go.get_hash_for_board(position.get_board())
        self.add_final_position_hash(game_id, hash)

    print('...Done')



def rebuild_board_hashes(self):
    print('Rebuilding board hashes...')

    self.clear_board_hashes()
    game_ids = self.get_all_game_id()

    count = 0

    hash_list = []
    for game_id in game_ids:
        count += 1
        if count % self.DISPLAY_MESSAGE_COUNT == 0:
            print(f'   ...{count} / {len(game_ids)}')
        # Get the moves and start a position
        moves = self.get_moves_for_game_id(game_id)
        position = game_of_go.Position.initial_state()
        color = game_of_go.BLACK
        move_number = 0
        # Loop through each move, build the position, save the hash
        try:
            for move in moves[:30]:
                move_number += 1
                position = position.play_move(move, color)
                color = game_of_go.swap_colors(color)
                hash = game_of_go.get_hash_for_board(position.get_board())
                try:
                    next_move = moves[move_number]
                except IndexError:
                    next_move = 'tt'
                hash_list.append((hash, game_id, move_number, next_move))
        except game_of_go.IllegalMove:
            print(f'   Game {game_id} has an invalid move at {move_number} - [{moves}]')
            continue

    print('Done processing games, inserting into database...')
    self.add_list_of_board_hash(hash_list)
    print('...Done')
