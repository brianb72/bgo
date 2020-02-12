import sqlite3



class DBAccessException(Exception):
    '''An unexpected and serious error while accessing the database'''

class DBAccessLookupNotFound(Exception):
    '''A game record or player lookup returned nothing'''

class DBAccessDuplicate(Exception):
    '''A game record or player that is being added already exists in the database'''

class DBAccessGameRecordError(Exception):
    '''A game record that is being parsed had invalid format, invalid data, or illegal moves'''

class DBAccess(object):
    DISPLAY_MESSAGE_COUNT = 100
    from database._sql import first_check_of_database, get_database_path, connect_to_sql
    from database._adding import add_games_from_tgz, add_game_record, add_final_position_hash
    from database._adding import add_list_of_board_hash
    from database._lookup import lookup_player_by_id, lookup_player_by_name, get_all_final_positions
    from database._lookup import get_all_game_id, get_moves_for_game_id, get_number_of_games_in_database
    from database._lookup import get_next_move_for_list_board_hash, merge_next_move_counter, get_next_move_counter_for_moves
    from database._maintenance import clear_final_positions, rebuild_final_positions
    from database._maintenance import clear_board_hashes, rebuild_board_hashes

    def __init__(self, database_path):
        self.database_path = database_path
        self.first_check_of_database()


