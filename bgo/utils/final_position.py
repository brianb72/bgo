from utils.sgf_parser import  SGFParser, SGFParserException
import game_of_go.coords as coords
import game_of_go.game_of_go as game_of_go

class FinalPosition(object):
    _final_pos = set()

    def __init__(self):
        pass

    '''
        Loads final positions returned from database.get_all_final_positions()
        Format is d[hash] = game_id
    '''
    def load_final_positions(self, dict_positions):
        for hash in dict_positions.keys():
            self._final_pos.add(hash)


    '''
        Test if the game is in unique
        Return True if it is unique and should be added to the database
        Return false if it is not unique and should be skipped
    '''
    def is_game_unique(self, sgf_object):
        rotated_hashes = []

        for rotation in range(0,8):
            position = game_of_go.build_positionsimple_from_move_pair_list(sgf_object.move_pair_list, rotation)
            hash = game_of_go.get_hash_for_board(position.get_board())
            if hash in self._final_pos:
                # The game is not unique, return False, it should not be added to the database
                return False
            rotated_hashes.append(hash)

        # The game is unique, return all hashes to the set
        for rotation in range(0,8):
            self._final_pos.add(rotated_hashes[rotation])

        # Return True, this game should be added to the database
        return True


