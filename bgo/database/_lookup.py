import sqlite3
from collections import Counter

from database import DBAccessException, DBAccessDuplicate, DBAccessGameRecordError, DBAccessLookupNotFound
import game_of_go.game_of_go as game_of_go
import game_of_go.coords as coords

'''
    Returns the number of games in the database
    Raises: DBAccessException
'''


def get_number_of_games_in_database(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = 'SELECT COUNT(*) from game_list'

    try:
        cursor.execute(query_string)
        result = cursor.fetchone()
    except DBAccessException as e:
        raise DBAccessException(f'error getting game count - [{e}]')

    return result[0]


'''
    Searches for a player by id and returns a string name
    Raises: DBAccessException, DBAccessLookupNotFound
'''
def lookup_player_by_id(self, player_id):
    if not isinstance(player_id, int):
        raise DBAccessException('lookup player passed non-integer')

    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = f'SELECT player_name FROM player_list WHERE player_id = {player_id}'

    try:
        cursor.execute(query_string)
        result = cursor.fetchone()
    except sqlite3.Error as e:
        raise DBAccessException(f'error looking up player - [{player_id}] - [{e}]')

    if result is None:
        raise DBAccessLookupNotFound()

    return result[0]

'''
    Searches for a player by name and returns an id
    Raises: DBAccessException, DBAccessLookupNotFound
'''
def lookup_player_by_name(self, player_name):
    if not isinstance(player_name, str):
        raise DBAccessException(f'error looking player up by name, not string - [{player_name}]')

    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = 'SELECT player_id FROM player_list WHERE player_name = \"%s\"' % (player_name,)
    try:
        cursor.execute(query_string)
        result = cursor.fetchone()
    except sqlite3.Error as e:
        raise DBAccessException(f'error looking up player by name - [{e}]')

    if result is None:
        raise DBAccessLookupNotFound()

    return result[0]

'''
    Returns all final positions in the format d[hash] = game_id
    Raises: DBAccessException
'''
def get_all_final_positions(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = 'SELECT board_hash, game_id FROM final_board_hash'

    try:
        cursor.execute(query_string)
        result = cursor.fetchall()
    except sqlite3.Error as e:
        raise DBAccessException(f'error getting all final positions - [{e}]')

    return {k:v for k,v in result}

'''
    Returns a list of all game_id's in the database
    Raises: DBaccessException
'''

def get_all_game_id(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        cursor.execute('SELECT game_id FROM game_list')
        result = cursor.fetchall()
    except sqlite3.Error as e:
        raise DBAccessException(f'error getting all game ids - [{e}]')
    if result is None:
        return []
    return [x[0] for x in result]

def get_moves_for_game_id(self, game_id):
    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = f'SELECT move_list FROM game_list WHERE game_id = {game_id}'
    try:
        cursor.execute(query_string)
        result = cursor.fetchone()
        if result == None:
            return DBAccessLookupNotFound(f'game not found while looking up moves for game {game_id}')
    except sqlite3.Error as e:
        raise DBAccessException(f'error looking up moves for game - [{e}]')

    return coords.convert_move_string_to_pair_list(result[0])


'''
    move_list = ['pd', 'dp']
    
    next_move_counter = Counter(
        'dd': 500,
        'ce': 375,
        'qf': 153,
        'de': 40
    )

    Each of the next_move's can be used with the move list to generate a 3 move position. ['pd', 'dp', 'dd'] etc
    Some of these positions may be rotations of each other.
    The larger position should eat the count of the smaller position.

'''

def merge_next_move_counter(self, move_list, next_move_counter):
    list_most_popular = [
        (next_move, count, game_of_go.build_hash_from_move_list(move_list + [next_move]))
        for next_move, count in
        next_move_counter.most_common()
    ]

    merged_counter = Counter()

    while len(list_most_popular) > 0:
        next_move, count, _ = list_most_popular.pop(0)
        merged_counter[next_move] = count
        rotated_hash_list = game_of_go.build_all_rotation_hashes_from_move_list(move_list + [next_move])
        for sub_next_move, sub_count, sub_hash in list(list_most_popular):
            if sub_hash in rotated_hash_list:
                merged_counter[next_move] += sub_count
                list_most_popular.remove((sub_next_move, sub_count, sub_hash))

    return merged_counter

def get_next_move_counter_for_moves(self, move_list, do_merge=True):
    to_identity_rotation = [0, 3, 2, 1, 4, 5, 6, 7]

    try:
        search_hashes = game_of_go.build_all_rotation_hashes_from_move_list(move_list)
    except game_of_go.IllegalMove:
        raise DBAccessException(f'error while getting next move counter, illegal move in [{move_list}]')

    search_hashes_str = [str(hash) for hash in search_hashes]
    query_string = f"SELECT board_hash, next_move FROM hash_list WHERE board_hash in ({', '.join(search_hashes_str)})"

    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        cursor.execute(query_string)
    except sqlite3.Error as e:
        raise DBAccessException(f'error building next_move_list for board_hash - [{e}]')

    counter_next = Counter()

    for row in cursor:
        board_hash = row[0]

        next_move = row[1]
        # Find the index of board_hash in list_board_hash, which will also tell us which rotation was used for this hash
        try:
            rotation = search_hashes.index(board_hash)
        except ValueError:
            raise DBAccessException(f'error building next_move_list could not find hash index')

        # Now rotate the move to the identity rotation
        identity_move = coords.transform_move_pair(next_move, to_identity_rotation[rotation])
        counter_next[identity_move] += 1

    if len(counter_next) == 0:
        raise DBAccessLookupNotFound(f'no next move data found')

    if do_merge:
        counter_next = self.merge_next_move_counter(move_list, counter_next)

    # Return the counter as a normal dictionary
    return counter_next



'''
    list_board_hash = [board_hash, ...]
    Return = {
    
    }
'''
def get_next_move_for_list_board_hash(self, list_board_hash):
    if not isinstance(list_board_hash, list):
        raise DBAccessException('list_board_hash must be list')
    list_to_str = [str(hash) for hash in list_board_hash if type(hash) == int]
    if len(list_to_str) != 8:
        raise DBAccessException('list_board_hash must be len == 8 and only integers')

    to_identity_rotation = [0, 3, 2, 1, 4, 5, 6, 7]

    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = f"SELECT board_hash, next_move FROM hash_list WHERE board_hash in ({', '.join(list_to_str)})"

    try:
        cursor.execute(query_string)
    except sqlite3.Error as e:
        raise DBAccessException(f'error building next_move_list for board_hash - [{e}]')

    counter_next = Counter()

    for row in cursor:
        board_hash = row[0]
        next_move = row[1]

        # Find the index of board_hash in list_board_hash, which will also tell us which rotation was used for this hash
        try:
            rotation = list_board_hash.index(board_hash)
        except ValueError:
            raise DBAccessException(f'error building next_move_list could not find hash index')

        # Now rotate the move to the identity rotation
        identity_move = coords.transform_move_pair(next_move, to_identity_rotation[rotation])
        counter_next[identity_move] += 1

    if len(counter_next) == 0:
        raise DBAccessLookupNotFound(f'no next move data found')

    # Return the counter as a normal dictionary
    return counter_next
