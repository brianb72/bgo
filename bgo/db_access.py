'''
bGo by BrianB (troff.troff@gmail.com)

db_access.py
    Provides SQLite3 database access

    Table List
        player_list         Player ID and Name
        game_list           Game data imported from SGF collection
        hash_list           Board hashes for every move from every game, and next move information
        final_board_hash    Final hash of every game with simplified rules of go for fast duplicate checks
        dyer_list           Dyer signatures for all games (not done)

    Exceptions
        DBAccessException           A serious SQL error
        DBAccessLookupNotFound      Lookup returned no results
        DBAccessDuplicate           Inserting a game that is already in the database
        DBAccessGameRecordError     game_of_go.IllegalMove raised or Index/Value errors during parsing of game data
'''

import os
import sqlite3
from bgo.sgf_parser import SGFParser, SGFParserException
import bgo.game_of_go as game_of_go
import bgo.preferred_rotation as pref_rotation
import bgo.coords as coords


class DBAccessException(Exception):
    '''An unexpected and serious error while accessing the database'''

class DBAccessLookupNotFound(Exception):
    '''A game record or player lookup returned nothing'''

class DBAccessDuplicate(Exception):
    '''A game record or player that is being added already exists in the database'''

class DBAccessGameRecordError(Exception):
    '''A game record that is being parsed had invalid format, invalid data, or illegal moves'''


class DBAccess(object):

    # ################################################################################################################
    # Create Statements

    CREATE_PLAYER_LIST = ('CREATE TABLE IF NOT EXISTS `player_list` ('
                          '`player_id`	INTEGER PRIMARY KEY AUTOINCREMENT,'
                          '`player_name`	TEXT NOT NULL UNIQUE);')

    CREATE_GAME_LIST = ('CREATE TABLE IF NOT EXISTS `game_list` ('
                        '`game_id`	INTEGER PRIMARY KEY,'
                        '`sgf_file_name`    TEXT NOT NULL,'
                        '`white_player_id`	INTEGER,'
                        '`white_rank`	INTEGER NOT NULL,'
                        '`black_player_id`	INTEGER,'
                        '`black_rank`	INTEGER NOT NULL,'
                        '`event`	TEXT,'
                        '`round`	TEXT,'
                        '`game_date`	DATE NOT NULL,'  # YYYY-MM-DD
                        '`place`	TEXT,'
                        '`komi`	TEXT,'
                        '`result`	TEXT NOT NULL,'
                        '`result_who_won`	INTEGER NOT NULL,'  # -1 = white   0 = unknown   1 = black
                        '`move_list_0` TEXT NOT NULL,'
                        '`move_list_1` TEXT NOT NULL,'
                        '`move_list_2` TEXT NOT NULL,'
                        '`move_list_3` TEXT NOT NULL,'
                        '`move_list_4` TEXT NOT NULL,'
                        '`move_list_5` TEXT NOT NULL,'
                        '`move_list_6` TEXT NOT NULL,'
                        '`move_list_7` TEXT NOT NULL'
                        ');')

    CREATE_DYER_LIST = ('CREATE TABLE IF NOT EXISTS `dyer_signatures` ('
                        '`game_id`	INTEGER NOT NULL,'
                        '`signature_a`	TEXT NOT NULL,'
                        '`signature_b`	TEXT NOT NULL,'
                        'PRIMARY KEY(`signature_a`,`signature_b`,`game_id`));')

    CREATE_HASH_LIST = ('CREATE TABLE IF NOT EXISTS `hash_list` ('
                        '`board_hash`	INTEGER NOT NULL,'
                        '`game_id`	INTEGER NOT NULL,'
                        '`move_number` INTEGER NOT NULL,'
                        '`next_move` TEXT NOT NULL);')  # the move number was played to generate this position and hash

    # A table containing the board hashes of the final boards of every game in the database, for quick unique checks.
    CREATE_FINAL_BOARD_HASH_LIST = ('CREATE TABLE IF NOT EXISTS `final_board_hash` ('
                                    '`board_hash`	INTEGER PRIMARY KEY,'
                                    '`game_id`	INTEGER NOT NULL);')

    CREATE_HASH_INDEX_1 = ('CREATE INDEX IF NOT EXISTS idx_hash_list ON hash_list (board_hash);')
    CREATE_HASH_INDEX_2 = ('CREATE INDEX IF NOT EXISTS idx_hash_list_move_number ON hash_list (move_number);')

    def __init__(self, database_path):
        self.database_path = database_path
        self.first_check_of_database()
        self._buffer_games_to_add = []

    # ################################################################################################################
    # Database Utility Functions

    '''
        Runs all create statements, which will silently be ignored if the tables exist.
        Call this before using the database for the first time to make sure it is initialized properly.
        Returns: DBAccessException
    '''

    def first_check_of_database(self):
        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(self.CREATE_PLAYER_LIST)
            cursor.execute(self.CREATE_GAME_LIST)
            cursor.execute(self.CREATE_DYER_LIST)
            cursor.execute(self.CREATE_HASH_LIST)
            cursor.execute(self.CREATE_FINAL_BOARD_HASH_LIST)
            cursor.execute(self.CREATE_HASH_INDEX_1)
            cursor.execute(self.CREATE_HASH_INDEX_2)
        except sqlite3.Error as e:
            raise DBAccessException('first_check_of_database() sql error [%s]' % (e,))

    '''
        Returns a string containing the full path to the database file
    '''

    def get_database_path(self):
        return self.database_path

    '''
        Attempt to open the database and return a connection object
        Raises: DBAccessException
    '''

    def connect_to_sql(self):
        try:
            con = sqlite3.connect(self.database_path)
        except sqlite3.Error:
            raise DBAccessException('sqlite3 error attempting to connect to database')
        return con

    '''
        Deletes all rows from the hash list table
        Raises: DBAccessException
    '''

    def clear_all_hashes(self):
        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute('DELETE FROM hash_list')
            db.commit()
        except sqlite3.Error as e:
            raise DBAccessException('dbaccess::clear_all_hashes() - SQLite error deleting rows [%s]' % (e,))

    '''
        Commit database transaction
    '''

    def do_commit(self):
        db = self.connect_to_sql()
        db.commit()

    # ################################################################################################################
    # Adding data to database

    '''
        Adds the game id and board hash to final board hash table, which uses simplified game of go to generate a fast
        position for duplicate checks
        Raises: DBAccessException
    '''

    def add_final_position_board_hash(self, game_id, board_hash):

        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'INSERT INTO final_board_hash (game_id, board_hash) VALUES (?,?)'

        try:
            db.execute(query_string, (game_id, board_hash))
            db.commit()

        except sqlite3.Error as e:
            raise DBAccessException('db_access::add_final_position_board_hash() - SQLite error adding hash [%s]' % (e,))

    '''
        Inserts a game record into the database. Adds the players to the player table if they are not in it.
        sgf_object is an SGFParser that has loaded a single sgf game record
        Returns the game id that was assigned to the newly inserted game.
        Raises: DBAccessException, DBAccessGameRecordError, DBAccessDuplicate, DBAccessLookupNotFound
    '''

    def add_game_record(self, sgf_object):
        if not isinstance(sgf_object, SGFParser):
            raise DBAccessException('db_access::add_game_record() - Passed non-GameRecord')

        # First check if this game is already in the database
        # Generate the hashes for the final board in all rotations
        try:
            final_hashes = [game_of_go.get_hash_for_board(
                game_of_go.build_positionsimple_from_move_pair_list(sgf_object.move_pair_list, rotation).get_board())
                            for rotation in range(8)]
            # final_hashes = [game_of_go.get_hash_for_board(game_of_go.build_position_from_move_pair_list(sgf_object.move_pair_list, rotation).get_board()) for rotation in range(8)]
        except game_of_go.IllegalMove as e:
            raise DBAccessGameRecordError(
                'db_access::add_game_record() - IllegalMove generating final_hashes [%s] [%s]' % (
                sgf_object.sgf_file_name, e))

        # Duplicate check, if we return a game_id the game is in our database, raise a Duplicate exception
        try:
            final_position_game_id = self.get_game_id_for_final_position(final_hashes)
            blurb = self.get_game_blurb(final_position_game_id)
            raise DBAccessDuplicate('Duplicate of [%i] [%s]' % (final_position_game_id, blurb))
        except DBAccessLookupNotFound:
            # Game is not in our database, continue
            pass

        # If using PositionSimple for final_hashes, we need to check the game here to verify it's valid with no
        #    IllegalMoves from ko or playing on top of stones. This is expensive but needed.
        try:
            position = game_of_go.build_position_from_move_pair_list(sgf_object.move_pair_list)
        except game_of_go.IllegalMove as e:
            raise DBAccessGameRecordError('db_access::add_game_record() - Game record has an IllegalMove [%s] [%s]' % (
            sgf_object.sgf_file_name, e))

        # Get the players names from the game
        black_player_name = sgf_object.get_black_name().strip()
        white_player_name = sgf_object.get_white_name().strip()

        # Get the players ranks
        try:
            black_player_rank = sgf_object.get_black_rank_as_int()
            white_player_rank = sgf_object.get_white_rank_as_int()
        except SGFParserException as e:
            raise DBAccessGameRecordError('dbaccess::add_game_record() - GameRecordException getting rank [%s] [%s]' % (
            sgf_object.sgf_file_name, e))

        # Lookup our players, or add them to the database.
        try:
            try:
                black_player_id = self.lookup_player_by_name(black_player_name)
            except DBAccessLookupNotFound:
                black_player_id = self.add_new_player(black_player_name)

            try:
                white_player_id = self.lookup_player_by_name(white_player_name)
            except DBAccessLookupNotFound:
                white_player_id = self.add_new_player(white_player_name)
        except DBAccessException as e:
            raise DBAccessGameRecordError(
                'db_access::add_game_record() - DBAccessException during player_id [%s] [%s]' % (
                sgf_object.sgf_file_name, e))

        # Create all rotations for the game
        try:
            rotated_move_list = [sgf_object.move_pair_list]
            for i in range(1, 8):
                rotated_move_list.append(coords.transform_move_pair_list(sgf_object.move_pair_list, i))
        except ValueError as e:
            raise DBAccessGameRecordError(
                'dbaccess::add_game_record() - ValueError while rotating moves, bad coordinates [%s] [%s]' % (
                sgf_object.sgf_file_name, e))

        # Try to determine who won
        try:
            who_won = sgf_object.get_who_won()
        except SGFParserException as e:
            who_won = 0
            # raise DBAccessException('dbaccess::add_game_record() - SGFParser Exception determining who won [%s]' % (e,))

        # Insert the record into the database
        try:
            db = self.connect_to_sql()
            cursor = db.cursor()

            query_string = (
                'INSERT INTO `game_list` (sgf_file_name, white_player_id, white_rank, black_player_id, black_rank,'
                'event, round, game_date, place, komi, result, result_who_won, move_list_0, move_list_1,'
                'move_list_2, move_list_3, move_list_4, move_list_5, move_list_6, move_list_7) VALUES '
                '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
            cursor.execute(query_string, (
            sgf_object.sgf_file_name, white_player_id, white_player_rank, black_player_id, black_player_rank,
            sgf_object.tag_dict['EV'].strip(),
            sgf_object.tag_dict['RO'].strip(),
            sgf_object.get_extracted_date(),
            sgf_object.tag_dict['PC'].strip(),
            sgf_object.tag_dict['KM'].strip(),
            sgf_object.tag_dict['RE'].strip(),
            who_won,
            coords.convert_move_pair_list_to_string(rotated_move_list[0]),
            coords.convert_move_pair_list_to_string(rotated_move_list[1]),
            coords.convert_move_pair_list_to_string(rotated_move_list[2]),
            coords.convert_move_pair_list_to_string(rotated_move_list[3]),
            coords.convert_move_pair_list_to_string(rotated_move_list[4]),
            coords.convert_move_pair_list_to_string(rotated_move_list[5]),
            coords.convert_move_pair_list_to_string(rotated_move_list[6]),
            coords.convert_move_pair_list_to_string(rotated_move_list[7])))
            db.commit()

            cursor.execute('SELECT last_insert_rowid()')
            game_id = cursor.fetchone()[0]

            self.add_final_position_board_hash(game_id, final_hashes[0])


        except sqlite3.Error as e:
            raise DBAccessException('db_access::add_game_record() - SQLite error adding game [%s]' % (e,))

        return game_id

    '''
        Adds a hash to the hash list.
        list_of_data = [board_hash, game_id, move_number, next_move]
        Raises: DBAccessException
    '''

    def add_new_hash(self, list_of_data):
        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'INSERT INTO hash_list (board_hash, game_id, move_number, next_move) VALUES (?, ?, ?, ?)'
        try:
            cursor.executemany(query_string, list_of_data)
            db.commit()
        except sqlite3.Error as e:
            raise DBAccessException('db_access:add_new_hash() - Error [%s]' % (e,))

    '''
        Adds a new player by name to the database, automatically asigning an ID
        Returns the ID of the newly added player
        Raises: DBAccessException
    '''

    def add_new_player(self, player_name):
        if not isinstance(player_name, str):
            raise DBAccessException('lookup_name() passed non-string')

        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'INSERT INTO player_list (player_name) VALUES (?)'
        try:
            cursor.execute(query_string, (player_name,))
            db.commit()
        except sqlite3.Error as e:
            raise DBAccessException('add_new_player() error during insert [%s]' % (e,))

        try:
            cursor.execute('SELECT last_insert_rowid()')
            new_id = cursor.fetchone()
            # TODO clean up, remove un-needed
            if new_id is None:
                raise DBAccessException('add_new_player() select last_insert_rowid is none')
            if len(new_id) != 1:
                raise DBAccessException('add_new_player() select last_insert_rowid is not 1')
        except sqlite3.Error as e:
            raise DBAccessException('add_new_player() error last_insert_rowid [%s]' % (e,))

        return new_id[0]

    # ################################################################################################################
    # String generation

    # Blurb is a quick string showing player names, date, event that can be printed on a single line
    '''
        Lookup the given game_id and return a short string showing player names, date, and the event.
        This string can be used as a blurb for a link, board with moves on it, or list of games.
        TODO: Enforce max length of blurb?
    '''

    def get_game_blurb(self, game_id):
        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT white_player_id, black_player_id, event, game_date FROM game_list WHERE game_id = %i' % (
        game_id,)
        try:
            cursor.execute(query_string)
            result = cursor.fetchone()
        except sqlite3.Error as e:
            raise DBAccessException('get_game_blurb() - sqlite error [%s]' % (e,))

        if result is None:
            raise DBAccessLookupNotFound()

        white_player_id = result[0]
        black_player_id = result[1]
        event = result[2]
        game_date = result[3]
        white_player_name = self.lookup_player_by_id(white_player_id)
        black_player_name = self.lookup_player_by_id(black_player_id)
        return "[%s] %s vs %s [%s]" % (game_date, white_player_name, black_player_name, event)

    # ################################################################################################################
    # Lookups


    '''
        Returns the number of games in the database
        Raises: DBAccessException
    '''
    def get_game_count(self):
        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT COUNT(*) from game_list'

        try:
            cursor.execute(query_string)
            result = cursor.fetchone()
        except DBAccessException as e:
            raise DBAccessException('db_access::get_game_count() - Error during lookup [%s]' % (e))

        return result[0]

    '''
        Searches for a player by id and returns a string name
        Raises: DBAccessException, DBAccessLookupNotFound
    '''

    def lookup_player_by_id(self, player_id):
        if not isinstance(player_id, int):
            raise DBAccessException('lookup_id() passed non-int')

        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT player_name FROM player_list WHERE player_id = %i' % (player_id,)

        try:
            cursor.execute(query_string)
            result = cursor.fetchone()
        except sqlite3.Error:
            raise DBAccessException('lookup_id() error during lookup')

        if result is None:
            raise DBAccessLookupNotFound()

        return result[0]

    '''
        Searches for a player by name and returns an id
        Returns: DBAccessException, DBAccessLookupNotFound
    '''

    def lookup_player_by_name(self, player_name):
        if not isinstance(player_name, str):
            raise DBAccessException('lookup_name() passed non-string')

        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT player_id FROM player_list WHERE player_name = \"%s\"' % (player_name,)
        try:
            cursor.execute(query_string)
            result = cursor.fetchone()
        except sqlite3.Error as e:
            raise DBAccessException('lookup_name() error during lookup [%s]' % (e,))

        if result is None:
            raise DBAccessLookupNotFound()

        return result[0]

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
            raise DBAccessException('get_all_games() - Error [%s]' % (e,))
        if result is None:
            return []
        return [x[0] for x in result]

    '''
        hash_list is a list of integers
        Search table `hash_list` for all game_id's that have any of the hashes
        Return a list of matching game_id's
        Raises: DBAccessException
    '''

    def search_game_id_for_hash_list(self, hash_list):
        if not isinstance(hash_list, list):
            raise DBAccessException('db_access::search_game_id_for_hash_list() - Passes non-list')

        hash_strings = ', '.join([str(i) for i in hash_list])

        query_string = 'SELECT game_id FROM hash_list WHERE board_hash IN (%s)' % (hash_strings)

        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(query_string)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('db_access::search_game_id_for_hash_list() - Error on query [%s]' % (e,))

        if result is None:
            return []
        return [x[0] for x in result]

    '''
        Used as a quick duplicate check
        final_hashes_all_rotations is a list of hashes
        Returns the game_id that matches any of the hashes, meaning the game is in the database
        Raises: DBAccessException, DBLookupNotFound
    '''

    def get_game_id_for_final_position(self, final_hashes_all_rotations):

        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT game_id FROM final_board_hash WHERE board_hash IN (?,?,?,?,?,?,?,?)'

        try:
            cursor.execute(query_string, final_hashes_all_rotations)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException(
                'db_access::is_final_position_in_database() - SQLite error during search [%s]' % (e,))

        if result == None or len(result) == 0:
            raise DBAccessLookupNotFound()

        return result[0][0]

    '''
        Search for all game_id's that have a single board_hash
        Returns a dictionary of { game_id: move_number }
        move_number is the move number of the last move that was played to generate the given hash
        Raises: DBAccessException
    '''

    def get_games_for_hash(self, board_hash, move_number=None):
        db = self.connect_to_sql()
        cursor = db.cursor()

        if move_number == None:
            query_string = 'SELECT game_id, move_number FROM hash_list WHERE board_hash = %i' % (board_hash,)
        else:
            query_string = 'SELECT game_id, move_number FROM hash_list WHERE board_hash = %i AND move_number = %i' % (
            board_hash, move_number)

        try:
            cursor.execute(query_string)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('db_access::get_games_for_hash() - Error [%s]' % (e,))

        return {game_id: move_number for game_id, move_number in result}

    '''
        Returns a list of game_id's whose move_list's start with the sequence in move_pair_list
        Raises: DBAccessException, DBAccessLookupNotFound        
    '''

    def search_game_id_starting_with_move_pair_list(self, move_pair_list):
        db = self.connect_to_sql()
        cursor = db.cursor()

        move_string = coords.convert_move_pair_list_to_string(move_pair_list) + '%'

        query_string = 'SELECT game_id FROM game_list WHERE %s ' % (
        " OR ".join(['move_list_%s LIKE ?' % (x,) for x in range(8)]),)
        try:
            cursor.execute(query_string, (
            move_string, move_string, move_string, move_string, move_string, move_string, move_string, move_string))
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('search_game_id_starting_with_move_pair_list() - Error [%s]' % (e,))
        if result is None:
            raise DBAccessLookupNotFound('search_game_id_starting_with_move_pair_list()')
        return [x[0] for x in result]

    """
        Search for games containing board_hash, then create a dictionary showing all possible next_move's.
        next_move is a single move such as 'pq' or 'dd'
        For each next_move create alist of game_id's that play next_move from board_hash
        Returned dictionary format is { next_move: game_id, ...] }
        Raises: DBAccessException, DBAccessLookupNotFound
    """

    def get_next_move_data_for_hash(self, board_hash):
        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT game_id, next_move FROM hash_list WHERE board_hash = %i' % (board_hash,)

        try:
            cursor.execute(query_string)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('db_access::get_next_move_data_for_hash() - Error searching for hash [%s]' % (e,))
        if result is None:
            raise DBAccessLookupNotFound()

        r = {}
        for game_id, next_move in result:
            try:
                r[next_move].append(game_id)
            except KeyError:
                r[next_move] = [game_id]

        return r

    '''
        Given a list of moves, search for players who played those moves in any rotation.
        Create a dictionary of format { player_name: number_of_games } where number_of_games is how many games
        the player has played the given moves in.
        Raises DBAccessException, DBLookupNotFound

    '''

    def get_players_for_move_pair_list(self, move_pair_list, all_rotations=False):
        # Consider what rotations to work with
        use_rotation_list = [0]
        if all_rotations == True:
            use_rotation_list.extend([1, 2, 3, 4, 5, 6, 7])

        db = self.connect_to_sql()
        cursor = db.cursor()

        player_dict = {}

        # Build positions and lookup for each rotation
        for rotation in use_rotation_list:
            rotated_board = game_of_go.build_position_from_move_pair_list(move_pair_list, rotation).get_board()
            board_hash = game_of_go.get_hash_for_board(rotated_board)

            sql_query = ('SELECT c.player_name as player_name FROM `hash_list` a'
                         ' INNER JOIN `game_list` as b'
                         ' ON a.game_id = b.game_id'
                         ' INNER JOIN `player_list` as c'
                         ' ON b.black_player_id = c.player_id'
                         ' WHERE board_hash = %i') % (board_hash,)

            try:
                cursor.execute(sql_query)
                result = cursor.fetchall()
            except sqlite3.Error as e:
                raise DBAccessException('db_access::get_year_dict_for_moves() - [%s]' % (e,))

            # If we get 0 results for a given rotations continue to the next rotation
            if result is None or len(result) == 0:
                continue

            # Iterate through the players we found and update the counts in the dictionary
            for player_name in [x[0] for x in result]:
                try:
                    player_dict[player_name] += 1
                except KeyError:
                    player_dict[player_name] = 1

        # If we found nothing in any rotation raise not found
        if len(player_dict) == 0:
            raise DBAccessLookupNotFound()

        return player_dict

    '''
        Creates a dictionary showing how many games exist in the database for each year.
        Dictionary format is { year: count }
        Raises: DBAccessException
    '''

    def get_number_of_games_by_year_dict(self):
        sql_query = ("SELECT year, count(*) FROM"
                     " (SELECT strftime('%Y', game_date) as year FROM game_list)"
                     " GROUP BY year"
                     " ORDER BY year ASC")

        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(sql_query)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('db_access::get_number_of_games_by_year_dict() - [%s]' % (e,))

        # If the database is empty, just return an empty dictionary, do not raise DBAccessLookupNotFound
        if result == None or len(result) == 0:
            return {}

        games_dict = {}
        for year, count in result:
            games_dict[year] = count

        return games_dict

    '''
        Returns a dictionary showing how many games exist per year starting with a given set of moves.
        Dictionary format is { year: count }
        Raises DBAccessException, DBAccessLookupNotFound
    '''

    def get_year_dict_for_moves(self, move_pair_list, all_rotations=False):
        year_dict = {}

        # Consider what rotations to work with
        use_rotation_list = [0]
        if all_rotations == True:
            use_rotation_list.extend([1, 2, 3, 4, 5, 6, 7])

        db = self.connect_to_sql()
        cursor = db.cursor()

        # Build positions and lookup for each rotation
        for rotation in use_rotation_list:
            rotated_board = game_of_go.build_position_from_move_pair_list(move_pair_list, rotation).get_board()
            board_hash = game_of_go.get_hash_for_board(rotated_board)
            sql_query = ("SELECT a.game_id as game_id, strftime('%%Y', b.game_date) as year FROM `hash_list` a"
                         " INNER JOIN `game_list` as b"
                         " ON a.game_id = b.game_id"
                         " WHERE a.board_hash = %i") % (board_hash,)

            try:
                cursor.execute(sql_query)
                result = cursor.fetchall()
            except sqlite3.Error as e:
                raise DBAccessException('db_access::get_year_dict_for_moves() - [%s]' % (e,))

            if result is None or len(result) == 0:
                continue

            for game_id, year in result:
                try:
                    year_dict[int(game_id)] = int(year)
                except TypeError as e:
                    # print('type error: %s game_id [%s] year [%s]' % (e,game_id,year))
                    continue

        if len(year_dict) == 0:
            raise DBAccessLookupNotFound('db_access::get_year_dict_for_moves() - Lookup not found')

        return year_dict

    '''
        Builds a position from moves, searches database for position, and creates a dictionary showing each next move
        played and the games that played that move.
        The next move coordinate for rotated positions are rotated back to the identity matrix.
        Dictionary is format { move_coordinate: [game_id, ...] }
        Raises: DBAccessException, DBAccessLookupNotFound

    '''

    def get_next_move_data_for_move_pair_list(self, move_pair_list, all_rotations=False):
        # For each of the 8 rotations, which rotation do we use to get to the identity rotation 011
        to_identity_rotation = [0, 3, 2, 1, 4, 5, 6, 7]

        use_rotation_list = [0]
        if all_rotations == True:
            use_rotation_list.extend([1, 2, 3, 4, 5, 6, 7])

        dict_ret = {}

        for rotation in use_rotation_list:
            rotated_board = game_of_go.build_position_from_move_pair_list(move_pair_list, rotation).get_board()
            board_hash = game_of_go.get_hash_for_board(rotated_board)
            dict_next_move = self.get_next_move_data_for_hash(board_hash)
            for next_move in dict_next_move.keys():
                count = len(dict_next_move[next_move])
                rotated_next_move = coords.transform_move_pair_list([next_move], to_identity_rotation[rotation])[0]

                try:
                    dict_ret[rotated_next_move].extend(dict_next_move[next_move])
                except KeyError:
                    # The game list from the unrotated next_move is added to the rotated next move list.
                    dict_ret[rotated_next_move] = dict_next_move[next_move]

        # game_id list is from all rotations, but rotated to the identity rotation
        # dict_ret[next_move] = [game_id, ...]
        return dict_ret

    '''
        Returns a list of all rotated move coordinates that are stored in the database for a specific game id.
        Raises DBAccessException, DBAccessLookupNotFound
    '''

    def get_all_move_pair_lists_for_game(self, game_id):
        db = self.connect_to_sql()
        cursor = db.cursor()

        query_string = 'SELECT move_list_0, move_list_1, move_list_2, move_list_3, move_list_4, move_list_5, move_list_6, move_list_7 FROM game_list WHERE game_id = ?'
        try:
            cursor.execute(query_string, (game_id,))
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('get_all_move_lists_for_game() - Error [%s]' % (e,))
        if result is None:
            raise DBAccessLookupNotFound('get_all_move_lists_for_game()')

        return [coords.convert_move_string_to_pair_list(result[0][rotation]) for rotation in range(8)]

    '''
        most_popular_moves_dict is created by get_most_popular_moves_xxx() functions
        The format is  { move_string: game_count }
        The dictionary contains games in all rotations. The same moves may appear in different rotated positions.
        This function iterates through the most_popular_moves_dict, identifies rotations that are the same, and merges 
        their game counts. Prefered rotations are used when possible.
        Returns a dictionary of format { move_string: game_count } where move_strings that are matching rotations are merged.
        This function is expensive and could use more optimization.
        Raises: Nothing   TODO add some error checking
    '''

    def merge_most_popular_moves_dict(self, most_popular_moves_dict):
        list_moves = list(most_popular_moves_dict.keys())

        final_counts = {}

        # Precreate a board for every position created by move_strings in most_popular_moves_dict.keys() / list_moves.
        dict_positions = {move_string: game_of_go.build_position_from_move_string(move_string).get_board() for
                          move_string in list_moves}

        # Main loop, consume list_moves
        while len(list_moves) > 0:

            # Pop off a move_string from the top of the list to work with, get it's count, and convert to a pair list
            popped_move_string = list_moves.pop(0)
            count = most_popular_moves_dict[popped_move_string]
            popped_move_pair_list = coords.convert_move_string_to_pair_list(popped_move_string)

            # Try to rotate the move_string to our preferred rotation
            rotated_move_pair_lists = [coords.transform_move_pair_list(popped_move_pair_list, rotation) for rotation in
                                       range(8)]
            pr = pref_rotation.pick_preferred_rotation(rotated_move_pair_lists)
            if pr > 0:
                # Found a better rotation, switch to it
                popped_move_pair_list = rotated_move_pair_lists[pr]
                popped_move_string = coords.convert_move_pair_list_to_string(popped_move_pair_list)

            # Use popped_move_string to generate all 8 rotated boards
            rotated_positions = [
                game_of_go.build_position_from_move_string(popped_move_string, rotation_number).get_board() for
                rotation_number in range(8)]

            # Step through the remaining list_moves. If a test_move_string builds a board that is in rotated_position then
            #    test_move_string is a rotated position of popped_move_string. Consume it's count and add it to be removed.
            to_remove = []
            for test_move_string in list_moves:
                if dict_positions[test_move_string] in rotated_positions:
                    to_remove.append(test_move_string)
                    count += most_popular_moves_dict[test_move_string]

            # Now remove the rotations we found from list_moves
            for test_move_string in to_remove:
                list_moves.remove(test_move_string)

            # Add this data to final_counts
            final_counts[popped_move_string] = count

        return final_counts

    '''
        Searchs the board_hash table for the most popular board hash
    '''

    def get_most_popular_positions_for_n_moves(self, n_moves):
        query = ('SELECT board_hash, count(board_hash) as c FROM hash_list WHERE move_number = %i GROUP BY board_hash'
                 ' ORDER BY c DESC' % (n_moves,))

        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('dbaccess::get_most_popular_positions_for_n_moves [%s]' % (e,))

        return result

    '''
        Searches the first N moves of every game in the database and returns the most popular move strings.
        Does not consider rotations, returns all strings raw.
        Use merge_most_popular_move_dict() to combine rotations into prefered rotations.
        Raises: DBAccessException
    '''

    def get_most_popular_moves_for_n_moves(self, n_moves):
        query = ('SELECT move_list, count(move_list) as game_count FROM (SELECT substr(move_list_0, 0, %i) as move_list'
                 ' FROM game_list) GROUP BY move_list ORDER BY game_count DESC') % (n_moves * 2 + 1,)

        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('dbaccess::get_most_popular_moves_for_n_moves [%s]' % (e,))

        return {k: v for k, v in result}

    '''
        Searches the first N moves of every game in the database between the date range and returns the most popular move strings.
        Does not consider rotations, returns all strings raw.
        Use merge_most_popular_move_dict() to combine rotations into prefered rotations.
        Raises: DBAccessException    
    '''

    def get_most_popular_moves_for_n_moves_by_year(self, n_moves, start_year, end_year):
        query = ("SELECT move_list, count(move_list) as game_count FROM (SELECT substr(move_list_0, 0, %i) as move_list"
                 " FROM game_list WHERE game_date BETWEEN '%i-1-1' AND '%i-12-31' ) GROUP BY move_list ORDER BY game_count DESC") \
                % (n_moves * 2 + 1, start_year, end_year)

        db = self.connect_to_sql()
        cursor = db.cursor()

        try:
            cursor.execute(query)
            result = cursor.fetchall()
        except sqlite3.Error as e:
            raise DBAccessException('dbaccess::get_most_popular_moves_for_n_moves_by_year [%s]' % (e,))

        return {k: v for k, v in result}

    '''
        Returns the move list for a given game in a given rotation
        Raises: DBAccessException, DBAccessLookupNotFound
    '''

    def get_move_list_for_game(self, game_id, rotation=0):
        db = self.connect_to_sql()
        cursor = db.cursor()

        if not isinstance(rotation, int) or rotation < 0 or rotation > 7:
            raise DBAccessException('dbaccess::get_move_list_for_game() - Invalid rotation')

        query_string = 'SELECT move_list_%i FROM game_list WHERE game_id = %i' % (rotation, game_id)
        try:
            cursor.execute(query_string)
            result = cursor.fetchone()
            if result == None or len(result) == 0:
                return DBAccessLookupNotFound('dbaccess::get_move_list_for_game() - [%i] not found' % (game_id,))
        except sqlite3.Error as e:
            raise DBAccessException('dbaccess::get_move_list_for_game() - SQLite error on lookup [%s]' % (e,))

        return coords.convert_move_string_to_pair_list(result[0])
