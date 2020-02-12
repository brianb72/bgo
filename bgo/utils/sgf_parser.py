'''
bGo by BrianB (troff.troff@gmail.com)

sgf_parser.py
    Uses PyGO's SGF library to parse an SGF file
    Extracts important tags to a local dictionary
    Decodes fields
    Can be directly inserted into bgo with db_access.add_game_record(sgf_parser_object)

    Numeric Ranks
        -30 = 30 kyu
         -1 = 1 kyu
          0 = Invalid Rank / Unranked Player
          1 = 1 dan
          9 = 9 dan
'''

import sgf
import re


class SGFParserException(Exception):
    """Raise whenever SGFParser has an error or exception"""

class SGFParser(object):
    def __init__(self):
        self.tag_dict = {
            'SZ': '',   # size of the board     '19'
            'PW': '',   # name of white         'Kimu Sujun'
            'WR': '',   # white rank            '8d'
            'PB': '',   # name of black         'Yamashita Keigo'
            'BR': '',   # black rank            '9d'
            'EV': '',   # event                 '33rd Tengen'
            'RO': '',   # round                 'Semi-final'
            'DT': '',   # date                  '2007-07-19'
            'PC': '',   # place                 'Nihon Ki-In, Tokyo'
            'KM': '',   # komi                  '6.5'
            'RE': '',   # result                'B+R'
        }
        self.tag_key_list = self.tag_dict.keys()
        self.sgf_file_name = ""
        self.move_pair_list = []
        self.extracted_date = None
        self._who_won = None    # -1 is white,  0 cannot be determined,  1 is black

    # ################################################################################################################
    # Utility


    '''
        Returns the move list as a string 'pqddqp'
    '''
    def get_move_list_as_string(self):
        return ''.join(self.move_pair_list)

    '''
        Imports a string 'pqddqp' as a move_pair_list ['pq', 'dd', 'qp']
    '''
    def import_string_to_move_list(self, string_moves):
        self.move_pair_list = [string_moves[i:i + 2] for i in range(0, len(string_moves), 2)]

    '''
        Sets a given tag to a value
    '''
    def set_tag(self, tag, value):
        self.tag_dict[tag] = value

    '''
        Gets the value of a tag
    '''
    def get_tag(self, tag):
        return self.tag_dict[tag]

    '''
        Gets the name of white player
    '''
    def get_white_name(self):
        return self.tag_dict['PW']

    '''
        Gets the name of black player
    '''
    def get_black_name(self):
        return self.tag_dict['PB']

    '''
        Decode result (RE) tag and determine who won
            -1 = white wins
             0 = cannot be determined
             1 = black wins
    '''
    def get_who_won(self):
        if self._who_won is None:
           if 'b' in self.tag_dict['RE'] or 'B' in self.tag_dict['RE']:
               self._who_won = 1
           elif 'w' in self.tag_dict['RE'] or 'W' in self.tag_dict['RE']:
               self._who_won = -1
           else:
                self._who_won = 0
                #raise SGFParserException('sgf_parser::get_did_black_win() - Could not determine.')
        return self._who_won


    # Decodes the DT field and returns a string of format 2005 or 2005-12 or 2005-12-30
    '''
        Decode the datetime (DT) field into a string of format
            "2005"
            "2005-12"
            "2005-12-30"
        This string is saved internally to self.extracted_date and is also returned.
    '''
    def get_extracted_date(self):
        year = 0
        month = 1
        day = 1

        # TODO regex to do this in one expression
        if self.extracted_date is None:
            match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', self.tag_dict['DT'])
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
            else:
                match = re.search(r'(\d{4})-(\d{1,2})', self.tag_dict['DT'])
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = 1
                else:
                    match = re.search(r'(\d{4})', self.tag_dict['DT'])
                    if match:
                        year = int(match.group(1))
                        month = 1
                        day = 1
                    else:
                        raise SGFParserException('sgf_parser::extract_date() could not decode date')
            self.extracted_date = '%4.4i-%2.2i-%2.2i' % (year, month, day)

        return self.extracted_date

    '''
        Given a rank string of format '15k' or '5d' return a numeric rank
        Numeric Ranks
            -30 = 30 kyu
             -1 = 1 kyu
              0 = Invalid Rank / Unranked Player
              1 = 1 dan
              9 = 9 dan
    '''
    def rank_string_to_numeric_rank(self, rank_string):
        if not isinstance(rank_string, str):
            raise SGFParserException('sgf_parser::rank_string_to_numeric_rank() passed non-string')

        for item in rank_string:
            if item.isalpha():
                rank_letter = item.upper()
                numeric_as_text = rank_string.split(item, 1)[0].strip()
                try:
                    numeric_rank = int(numeric_as_text)
                except ValueError:
                    return 0
                if numeric_rank > 30 or numeric_rank < 1:
                    return 0
                if rank_letter == 'D':
                    return numeric_rank
                if rank_letter == 'K':
                    return -numeric_rank
                else:
                    return 0

        return 0

    '''
        Gets the black rank as an integer
    '''
    def get_black_rank_as_int(self):
        return self.rank_string_to_numeric_rank(self.tag_dict['BR'])

    '''
        Gets the white rank as an integer
    '''
    def get_white_rank_as_int(self):
        return self.rank_string_to_numeric_rank(self.tag_dict['WR'])

    '''
        Given a string containing the contents of an sgf file, decode it using PyGO's SGF 
        library and then extract data to our internal dictionary.
    '''
    def import_from_sgf_file_text(self, sgf_file_text, sgf_file_name=""):
        try:
            game_collection = sgf.parse(sgf_file_text)
        except (sgf.ParseException, UnboundLocalError) as e:
            raise SGFParserException(f'sgf_parser::import_from_sgf_file_text() - [{e}]')
        if (len(game_collection) != 1):
            raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Game collection must have only one game record.')

        if len(game_collection[0].nodes) <= 0:
            raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Game record must have more than 0 nodes.')

        # Copy the file name and save all tags
        self.sgf_file_name = sgf_file_name
        for k, v in game_collection[0].root.properties.items():
            k = k.upper()
            if k in self.tag_key_list:
                self.tag_dict[k] = v[0]

        # Parse the date, this function stores it's result in self.extracted_date and it's return can be ignored
        try:
            self.get_extracted_date()
        except SGFParserException:
            raise SGFParserException('sgf_parser::import_from_sgf_file_text() - could not parse date')

        # Iterate the moves and save them as a move_pair_list, they must always alternate B W B W or reject the file
        last_move = 'W'
        for node in game_collection[0].rest:
            if len(node.properties) != 1:
                raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Node list contained a move with more than one property')
            if (last_move == 'W'):
                if 'B' not in node.properties:
                    raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Move in move list expected to be B, was not found.')
                node_len = len(node.properties['B'][0])
                if node_len == 2:
                    self.move_pair_list.append(node.properties['B'][0].lower())
                elif node_len == 0:   # A small number of games have a blank move to indicate a pass
                    self.move_pair_list.append('tt')
                else:
                    raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Invalid move found.')
                last_move = 'B'
            else: # last_move == 'B'
                if 'W' not in node.properties:
                    raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Move in move list expected to be W, was not found.')
                node_len = len(node.properties['W'][0])
                if node_len == 2:
                    self.move_pair_list.append(node.properties['W'][0].lower())
                elif node_len == 0: # A small number of games have a blank move to indicate a pass
                    self.move_pair_list.append('tt')
                else:
                    raise SGFParserException('sgf_parser::import_from_sgf_file_text() - Invalid move found.')
                last_move = 'W'







