import sqlite3
import os
import tarfile

from utils.sgf_parser import SGFParser, SGFParserException
from database import DBAccessException, DBAccessDuplicate, DBAccessGameRecordError, DBAccessLookupNotFound
from game_of_go import game_of_go, coords

from utils.final_position import FinalPosition



def add_games_from_tgz(self, path_to_tgz):
    print(f'Importing games...')

    sgf_count = 0
    sgf_added = 0
    sgf_duplicate = 0
    sgf_parse_error = 0
    sgf_failed = 0

    final_pos = FinalPosition()
    try:
        final_pos.load_final_positions(self.get_all_final_positions())
    except DBAccessException as e:
        raise DBAccessException(f'error adding games from tgz, failed to load final positions - [{e}]')

    db = self.connect_to_sql()
    cursor = db.cursor()

    try:
        tar = tarfile.open(path_to_tgz, 'r:gz')
    except OSError as e:
        raise DBAccessException(f'error importing tgz, cannot open - [{path_to_tgz}]')

    try:
        files_in_tar = sum(1 for member in tar if member.isreg())
        processed = 0
        for tarinfo in tar:
            processed += 1
            if processed % self.DISPLAY_MESSAGE_COUNT == 0:
                print(f'...Processed {processed} / {files_in_tar} ({processed / files_in_tar * 100:.0f}%)')
            _, extension = os.path.splitext(tarinfo.name)
            if extension.lower() != '.sgf':
                continue
            reader = tar.extractfile(tarinfo)
            sgf_data = reader.read().decode('utf-8')
            sgf = SGFParser()
            try:
                sgf.import_from_sgf_file_text(sgf_data, tarinfo.name)
            except SGFParserException as e:
                # print(f'error parsing game from tar - [{tarinfo.name}] - [{e}]')
                sgf_parse_error += 1
                continue

            sgf_count += 1

            if final_pos.is_game_unique(sgf) == False:
                print(f'{tarinfo.name} duplicate, ignoring.')
                sgf_duplicate += 1
                continue

            try:
                self.add_game_record(cursor, sgf)
                sgf_added += 1
            except DBAccessException as e:
                print(f'exception while adding game record - [{tarinfo.name}] - [{e}]')
                sgf_failed += 1
                continue
            except DBAccessGameRecordError as e:
                print(f'game record error while adding game - [{tarinfo.name}] - [{e}]')
                sgf_failed += 1
                continue

    except EOFError as e:
        raise DBAccessException(f'error importing tgz, EOFError while processing - [{path_to_tgz}] - [{e}]')

    try:
        db.commit()
    except DBAccessException as e:
        raise DBAccessException(f'error importing tgz, failed on final commit [{path_to_tgz}] - [{e}]')

    return (sgf_count, sgf_added, sgf_duplicate, sgf_parse_error, sgf_failed)

def add_game_record(self, db_cursor, sgf_object):
    if not isinstance(sgf_object, SGFParser):
        raise DBAccessException(f'error adding new game - Passed non-GameRecord')

    # Get the players names from the game
    black_player_name = sgf_object.get_black_name().strip()
    white_player_name = sgf_object.get_white_name().strip()

    # Get the players ranks
    try:
        black_player_rank = sgf_object.get_black_rank_as_int()
        white_player_rank = sgf_object.get_white_rank_as_int()
    except SGFParserException as e:
        raise DBAccessGameRecordError(f'error adding new game - GameRecordException getting rank - [{sgf_object.sgf_file_name}] [{e}]')

    # Try to determine who won
    try:
        who_won = sgf_object.get_who_won()
    except SGFParserException as e:
        who_won = 0

    # Insert the record into the database
    try:
        query_string = (
            'INSERT INTO `game_list` (sgf_file_name, white_player_name, white_player_rank, black_player_name, black_player_rank,'
            'event, round, game_date, place, komi, result, result_who_won, move_list) VALUES '
            '(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        db_cursor.execute(query_string, (
            sgf_object.sgf_file_name, white_player_name, white_player_rank, black_player_name, black_player_rank,
            sgf_object.tag_dict['EV'].strip(),
            sgf_object.tag_dict['RO'].strip(),
            sgf_object.get_extracted_date(),
            sgf_object.tag_dict['PC'].strip(),
            sgf_object.tag_dict['KM'].strip(),
            sgf_object.tag_dict['RE'].strip(),
            who_won,
            coords.convert_move_pair_list_to_string(sgf_object.move_pair_list)
            ))
        db_cursor.execute('SELECT last_insert_rowid()')
        game_id = db_cursor.fetchone()[0]
    except sqlite3.Error as e:
        raise DBAccessException(f'error adding new game - SQLite error adding game [{e}]')
    return game_id

def add_final_position_hash(self, game_id, board_hash):
    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = 'INSERT INTO final_board_hash (game_id, board_hash) VALUES (?,?)'

    try:
        db.execute(query_string, (game_id, board_hash))
        db.commit()
    except sqlite3.Error as e:
        raise DBAccessException('db_access::add_final_position_board_hash() - SQLite error adding hash [%s]' % (e,))

'''
    list_board_hash_data = [ (board_hash, game_id, move_number, next_move), ... ]
'''
def add_list_of_board_hash(self, list_board_hash_data):
    db = self.connect_to_sql()
    cursor = db.cursor()

    query_string = 'INSERT INTO hash_list (board_hash, game_id, move_number, next_move) VALUES (?,?,?,?)'

    try:
        db.executemany(query_string, list_board_hash_data)
        db.commit()
    except sqlite3.Error as e:
        raise DBAccessException(f'error adding bulk board hashes - [{e}]')
