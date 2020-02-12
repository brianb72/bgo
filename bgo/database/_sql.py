import sqlite3
from database import DBAccessDuplicate, DBAccessException, DBAccessGameRecordError, DBAccessLookupNotFound

CREATE_PLAYER_LIST = ('CREATE TABLE IF NOT EXISTS `player_list` ('
                      '`player_id`	INTEGER PRIMARY KEY AUTOINCREMENT,'
                      '`player_name`	TEXT NOT NULL UNIQUE);')

CREATE_GAME_LIST = ('CREATE TABLE IF NOT EXISTS `game_list` ('
                    '`game_id`	INTEGER PRIMARY KEY,'
                    '`sgf_file_name`    TEXT NOT NULL,'
                    '`white_player_name`	TEXT NOT NULL,'
                    '`white_player_rank`	INTEGER NOT NULL,'
                    '`black_player_name`	TEXT NOT NULL,'
                    '`black_player_rank`	INTEGER NOT NULL,'
                    '`event`	TEXT,'
                    '`round`	TEXT,'
                    '`game_date`	DATE NOT NULL,'  # YYYY-MM-DD
                    '`place`	TEXT,'
                    '`komi`	TEXT,'
                    '`result`	TEXT NOT NULL,'
                    '`result_who_won`	INTEGER NOT NULL,'  # -1 = white   0 = unknown   1 = black
                    '`move_list` TEXT NOT NULL'
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

'''
    Runs all create statements, which will silently be ignored if the tables exist.
    Call this before using the database for the first time to make sure it is initialized properly.
    Returns: DBAccessException
'''
def first_check_of_database(self):
    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        cursor.execute(CREATE_PLAYER_LIST)
        cursor.execute(CREATE_GAME_LIST)
        cursor.execute(CREATE_DYER_LIST)
        cursor.execute(CREATE_HASH_LIST)
        cursor.execute(CREATE_FINAL_BOARD_HASH_LIST)
        cursor.execute(CREATE_HASH_INDEX_1)
        cursor.execute(CREATE_HASH_INDEX_2)
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
    except sqlite3.Error as e:
        raise DBAccessException('sqlite3 error attempting to connect to database')
    return con

