'''
    bGo by BrianB (troff.troff@gmail.com)

    openingbook.py
        python -m reports.openingbook

        Rough draft of report generator. CSS/HTML has a lot of extra stuff in it from testing. Eventually will
        replace JGO with SVG, do a rewrite then.

        Generates a set of HTML pages that enumerate the most popular moves 4-7 with next move data.
        Pages are sorted into chapters based on first four moves.
        Table of contents shows all chapters.
        Boards are drawn using JGO javascript (https://github.com/jokkebk/jgoboard)
        TODO replace javascript with SVG
'''

from bgo.db_access import DBAccess, DBAccessException, DBAccessLookupNotFound
import bgo.coords as coords
import bgo.diagrams as diagrams
import bgo.game_of_go as game_of_go
import bgo.preferred_rotation as pref_rotation
import collections
import json
import copy

from datetime import datetime

db = DBAccess('baduk.sqlite')

class BuildNextMoveJSON(object):
    root_nodes = []
    nodes_to_process = []
    output_json = None

    def search_base_position(self, num_of_moves, search_date_earliest=1, search_date_latest=9999, cached=False):
        time_start = datetime.now()
        print('--- Starting search_base_position')
        if not cached:
            # Setup the initial search
            print('   Searching for most popular moves by year.')
            time_search_start = datetime.now()
            raw_most_popular_moves_dict = db.get_most_popular_moves_for_n_moves_by_year(num_of_moves, search_date_earliest,
                                                                                        search_date_latest)
            time_search_end = datetime.now()
            print(f'   ...finished {time_search_end - time_search_start}')

            print('   Merging positions.')
            time_merge_start = datetime.now()
            most_popular_moves_dict = db.merge_most_popular_moves_dict(raw_most_popular_moves_dict)
            sorted_most_popular_moves_index = sorted(most_popular_moves_dict, key=lambda k: most_popular_moves_dict[k],
                                                     reverse=True)
            time_merge_end = datetime.now()
            print(f'   ...finished {time_search_end - time_search_start}')

            #print('Finished Merging')
            #with open('raw_opening_data.json', 'w') as fp:
            #    json.dump((most_popular_moves_dict, sorted_most_popular_moves_index), fp)
        else:
            print('CACHE DISABLED')
            return
            #with open('raw_opening_data.json', 'r') as fp:
            #    most_popular_moves_dict, sorted_most_popular_moves_index = json.load(fp)

        time_end = datetime.now()
        print(f'--- Finished search_base_position in {time_end - time_start}')

        return (most_popular_moves_dict, sorted_most_popular_moves_index)

    base_move_data_dict = {
        'move_list': [],            # Move list that generated the board for this node
        'node_count': 0,            # How many games are held under this node
        'mark_letter': None,        # Mark letter for this node
        'mark_coord': None,         # Coordinate for any mark
        'next_node': [],           # A list of sub_nodes for the next move, ordered 'A', 'B', 'C', ...
        'depth': 0,                 # 0 is the root node, 1 is next_moves, 2 is next_moves of next_moves, etc
    }

    """
        search_depth    How many steps deep to search
        limit_root               variations on root node
        limit_sub                varations on sub nodes
    """
    def build_node(self, work_node, limit_depth = 1, limit_root = 6, limit_sub = 6):
        if work_node['depth'] > limit_depth:
            return

        if work_node['depth'] == 0:
            use_limit = limit_root
        else:
            use_limit = limit_sub

        if use_limit < 0 or use_limit > 26:
            raise ValueError('Limits must be 0 - 26')


        # d['pq'] = [game_id, ...]
        next_moves_dict = db.get_next_move_data_for_move_pair_list(coords.convert_move_string_to_pair_list(work_node['move_list']), all_rotations=True)
        sorted_next_move = sorted(next_moves_dict, key=lambda k: len(next_moves_dict[k]), reverse=True)

        next_depth = work_node['depth'] + 1
        mark_counter = 0
        total_count = 0

        for next_move in sorted_next_move[:use_limit]:
            next_node = copy.deepcopy(self.base_move_data_dict)
            next_node['move_list'] = work_node['move_list'] + next_move
            next_node['node_count'] = len(next_moves_dict[next_move])
            next_node['mark_letter'] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[mark_counter]
            mark_counter += 1
            next_node['mark_coord'] = next_move
            next_node['depth'] = next_depth
            total_count += len(next_moves_dict[next_move])

            # Add to lists
            work_node['next_node'].append(next_node)
            self.nodes_to_process.append(next_node)

        # Update parent total count
        work_node['node_count'] = total_count


    # ENTRY POINT
    def do_build(self):
        # Search for the first N moves
        # most_popular_opening_dict['pdddqpdq'] = 5000   key move list, value game count
        most_popular_opening_dict, sorted_most_popular_moves_index = self.search_base_position(4, 1920, 2020, False)

        time_build_start = datetime.now()

        print('   Begining build...')
        # Add the root nodes to the processing list
        for move_list in sorted_most_popular_moves_index[:12]:
            node = copy.deepcopy(self.base_move_data_dict)
            node['move_list'] = move_list
            self.root_nodes.append(node)
            self.nodes_to_process.append(node)

        # Loop through the to process list until empty
        while len(self.nodes_to_process) > 0:
            node = self.nodes_to_process.pop()
            self.build_node(node, limit_depth=3, limit_root=6, limit_sub=6)

        self.output_json = self.root_nodes

        time_build_end = datetime.now()
        print(f'   ...build finished in {time_build_end - time_build_start}')

        #with open('next_move_dict.json', 'w') as fp:
        #    json.dump(self.root_nodes, fp)

        print('Done.')



# ########################################################
#
#

'''

                                                DEFINITIONS
                                                -----------


"First Four" chapters
    Cover Sheet
        Each "First Four" move will have a cover sheet marking the start of the first four chapter. The first four
        board and letterboard will be large and on the top. 
    Chapter Sheet
        A "First Four" chapter is broken into "Move Five" subchapters.
        The chapter for an individual "First Four" will start with a wide row showing the most popular "Move Five" diagram.
        Then a row will start with a "Move Six" diagram followed by multiple "Move Seven" diagrams.
        The second most popular "Move Five" diagram will start, followed by "Move Six" and "Move Seven" like before.
        Repeat until "Move Five" are all done.
        End of chapter, begin another "First Four" cover sheet for next chapter.





First Four
    The first four moves of a game, and the letterboard showing popular move 5's.

Move Five @ <letter>
    Major header, full row
    The first five moves of a game, and the letter board showing popular move 6's.

Move Six @ <letter>
    Minor header

Move Seven @ <letter>
    Data item


                                                    LAYOUT
                                                    ------

"Table Of Contents" sheets
    Loads a most popular moves json
    Displays a grid showing the most popular first four moves which the letterboard showing move 5
    Each first four is just a datapoint in a chart and maybe some sort of page number for the printed version?
    These pages would go first in a binder or stapled stack.
'''

css_table_of_contents = '''
    <style>
        .table_of_contents > div {
            text-align: center;
        }

        .table_of_contents {
            display: grid;
            grid-template-columns: repeat(3, [col] minmax(20px, 1fr));
            grid-gap: 40px 20px;
        }

        .move_five > div {
            text-align: center;
        }

        .move_five {
            grid-column-start: 1;
            grid-column-end: 4;
            border: 1px solid rgb(0,0,0);
            border-radius: 1px;
        }

        .move_six {
            grid-column-start: 1;
            grid-column-end: 2;
        }

        .new_row {
            grid-column-start: 1;
            grid-column-end: 2;        
        }

        .chapter_grid > div {
            text-align: center;
        }

        .chapter_grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-gap: 10px 5px;
        }

        .split_cell_toc {
            display: grid;
            grid-template-columns: 0% 70% 30% 0%;
            //border: 1px solid rgb(0,0,0);
            //border-radius: 1px;
            padding: 30px 5px;
        }

        .split_cell {
            display: grid;
            grid-template-columns: 0% 70% 30% 0%;
            padding: 2px 5px;
        }

        .border {
            border: 1px solid rgb(0,0,0);
            border-radius: 1px;
        }

        .split_cell > div {
            text-align: center;
        }



        .split_next_move > div {
            text-align: center;
            //border-radius: 1px;
            //border: 1px solid rgb(0,0,0);
        }

        .split_next_move {
            display: grid;
            grid-template-columns: 50% 50%;
            grid-gap: 1px;
        }

        .limit_width {
            width: 33%;
        }

        .text_right {
            text-align: right;
        }
    </style>
'''

css_chapter = '''
    <style>

    </style>
'''

css_style = '''
    <style>
        .container > div {
            //border-radius: 1px;
            padding: 3px;
            //border: 2px solid rgb(0,0,0);
            text-align: center;

        }
        .container {
            display: grid;
            grid-template-columns: repeat(3, [col] minmax(50px, 1fr));
            grid-template-rows: [row] auto;
            grid-gap: 6px;
        }

        .cell_contents { 
            display: grid;
            grid-template-columns: 2;
            grid-template-rows: 1;
        }

        .move_list > div {
            //border-radius: 2px;
            //padding: 1px;
            //border: 2px solid rgb(0,0,0);
        }

        .move_list {
            display: grid;
            grid-template-columns: repeat(2, [col] 1fr);
            grid-auto-rows: [row] auto;
            grid-gap: 1px;
        }

        .pattern-initial-header {
            border-radius: 1px;
            border: 6px solid rgb(0,0,0);
            grid-area: span 3 / span 3;
        }

        .pattern-opening-header {
            border-radius: 1px;
            //padding: 3px;
            border: 4px solid rgb(0,0,0);
            grid-column: span 3;
        }

        .pattern-variation-header {
            border-radius: 1px;
            //padding: 3px;
            border: 2px solid rgb(0,0,0);
        }

        .pattern-final-header {

        }

        .pattern-variation-header + .pattern-opening-header {
            grid-column-start: 1;
        }

        .pattern-final-header + .pattern-variation-header {
            grid-column-start: 1;
        }



    </style>  
'''

NUMBER_NAMES = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten']
LIMIT_MARK_BOARD = 6

# #########################################################################################################


opening_counter = 0


def process_toc_node(fp, node):
    move_pair_list = coords.convert_move_string_to_pair_list(node['move_list'])

    total_games = node['node_count']
    mark_board_dict = {d['mark_coord']: d['mark_letter'] for d in node['next_node']}

    global opening_counter
    opening_counter += 1

    blurb = 'First Four %i: %i games' % (opening_counter, total_games)

    fp.write('   <div class="split_cell_toc">\n')
    fp.write('      <div>&nbsp;</div>\n')
    fp.write('      ' + diagrams.string_div_open_small_blurb % ('', blurb) + '\n')
    fp.write('      ' + diagrams.make_diagram_with_mark_board(move_pair_list, mark_board_dict) + '\n')
    fp.write('      ' + diagrams.string_div_close + '\n')
    fp.write('    <div class="split_next_move">\n')

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    for row in node['next_node']:
        fp.write('      <div>%s:</div>\n' % (row['mark_letter'],))
        fp.write('      <div>%.1f%%</div>\n' % (float(row['node_count']) / total_games * 100.0,))

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    fp.write('    </div>\n')  # split_next_move
    fp.write('      <div>&nbsp;</div>\n')

    fp.write('   </div>\n')  # split_cell


def write_table_of_contents(fp, root_nodes_dict):
    sorted_keys = sorted(root_nodes_dict, key=lambda d: d['node_count'], reverse=True)

    # HTML HEADER and start of grid
    fp.write(diagrams.string_document_open_with_style % (css_table_of_contents,) + '\n')
    fp.write('<div class="table_of_contents">\n')

    # BODY
    for root_node in sorted_keys:
        process_toc_node(fp, root_node)

    # FOOTER
    fp.write('</div>')  # table_of_contents
    fp.write(diagrams.string_document_close + '\n')


'''
    A chapter is a root node, which is a "First Four"
    chapter_node['next_node'] are the "Move Five" charts
    chapter_node['next_node'][x]['next_node'] are the "Move Six"


    pattern is
    "Move Five" big row
        "Move Six" small block
            "Move Seven" data point

'''


def write_chapter_five(fp, node, title_text=None):
    move_pair_list = coords.convert_move_string_to_pair_list(node['move_list'])
    total_games = node['node_count']
    mark_board_dict = {d['mark_coord']: d['mark_letter'] for d in node['next_node']}
    blurb = 'Move Five @ %s: %i games' % (node['mark_letter'], total_games)

    if title_text == None:
        fp.write('  <div class="new_row">&nbsp;</div>\n')
    else:
        fp.write('   <div class="new_row" style="text-align: center;"><h1>%s</h1></div>\n' % (title_text,))
    fp.write('   <div class="split_cell">\n')
    fp.write('      <div>&nbsp;</div>\n')
    fp.write('      ' + diagrams.string_div_open_small_blurb % ('', blurb) + '\n')
    fp.write('      ' + diagrams.make_diagram_with_mark_board(move_pair_list, mark_board_dict) + '\n')
    fp.write('      ' + diagrams.string_div_close + '\n')
    fp.write('    <div class="split_next_move">\n')

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    for row in node['next_node']:
        fp.write('      <div>%s:</div>\n' % (row['mark_letter'],))
        fp.write(
            '      <div style="text-align: right">%.1f%%</div>\n' % (float(row['node_count']) / total_games * 100.0,))

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    fp.write('    </div>\n')  # split_next_move
    fp.write('      <div>&nbsp;</div>\n')

    fp.write('   </div>\n')  # split_cell


def write_chapter_item(fp, node, is_move_six=False):
    move_pair_list = coords.convert_move_string_to_pair_list(node['move_list'])
    total_games = node['node_count']
    mark_board_dict = {d['mark_coord']: d['mark_letter'] for d in node['next_node']}

    if is_move_six:
        blurb = 'Move 6 @ %s: %i games' % (node['mark_letter'], total_games)
        fp.write('   <div class="split_cell move_six border">\n')
    else:
        blurb = 'Move 7 @ %s: %i games' % (node['mark_letter'], total_games)
        fp.write('   <div class="split_cell">\n')

    fp.write('      <div>&nbsp;</div>\n')
    fp.write('      ' + diagrams.string_div_open_small_blurb % ('', blurb) + '\n')
    fp.write('      ' + diagrams.make_diagram_with_mark_board(move_pair_list, mark_board_dict) + '\n')
    fp.write('      ' + diagrams.string_div_close + '\n')
    fp.write('    <div class="split_next_move">\n')

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    for row in node['next_node']:
        fp.write('      <div>%s:</div>\n' % (row['mark_letter'],))
        fp.write(
            '      <div style="text-align: right;">%.1f%%</div>\n' % (float(row['node_count']) / total_games * 100.0,))

    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')
    fp.write('      <div>&nbsp;</div><div>&nbsp;</div>\n')

    fp.write('    </div>\n')  # split_next_move
    fp.write('      <div>&nbsp;</div>\n')

    fp.write('   </div>\n')  # split_cell


'''
    node is a 'first four' root node from json_data[x]
    node['next_node'] is 'Move Five', a major header
    node['next_node']['next_node'] is 'Move Six', a minor header
    node['next_node']['next_node']['next_node'] is 'Move Seven', a data point
'''


def write_chapter(fp, chapter_node, chapter_title):
    # HTML HEADER and start of grid
    fp.write(diagrams.string_document_open_with_style % (css_table_of_contents,) + '\n')
    fp.write('<div class="chapter_grid">\n')

    title_once = False

    for move_five in chapter_node['next_node']:
        if title_once == True:
            write_chapter_five(fp, move_five)
        else:
            write_chapter_five(fp, move_five, chapter_title)
            title_once = True;
        for move_six in move_five['next_node']:
            write_chapter_item(fp, move_six, True)
            for move_seven in move_six['next_node'][:5]:
                write_chapter_item(fp, move_seven, False)

    # FOOTER
    fp.write('</div>')  # table_of_contents
    fp.write(diagrams.string_document_close + '\n')





if __name__ == '__main__':
    # Generate next move json data
    bnm = BuildNextMoveJSON()
    bnm.do_build()
    json_data = bnm.output_json

    # Write the HTML Data
    # Write the table of contents
    print('Writing TOC...')
    with open('HTML/toc.html', 'w') as fp:
        write_table_of_contents(fp, json_data)

    chapter_count = len(json_data)
    print('Writing %i chapters...' % (chapter_count,))

    for chapter in range(chapter_count):
        file_name = 'HTML/chapter_%i.html' % (chapter + 1,)
        print('   Writing %s' % (file_name,))
        with open(file_name, 'w') as fp:
            write_chapter(fp, json_data[chapter], 'First Four #%i' % (chapter + 1,))

    print('Done.')
