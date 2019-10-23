import os
import tarfile
from datetime import datetime

from bshell.commands import Command
import bgo.sgf_parser as sgf_parser
from bgo.db_access import DBAccess, DBAccessGameRecordError, DBAccessLookupNotFound, DBAccessException, DBAccessDuplicate

class Import(Command):

    keywords = ['import']
    help_text = """{keyword}
{divider}
Summary: Imports a tgz of SGF files into the current database.

Usage: {keyword} <file>

Examples:

    {keyword} game-collection.tgz
"""

    def do_command(self, *args):
        if not args and len(args) is not 1:
            print(f'Needs a file to import.')
            return

        arg_path = args[0]

        if os.path.abspath(arg_path):
            import_path = arg_path
        else:
            import_path = os.path.join(self.state.working_dir, arg_path)

        if not os.path.isfile(import_path):
            print(f'Could not find file {import_path}')
            return

        print(f'\n\n*** About to import {import_path}')
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

        print('Begining import...')

        # Open the archive
        try:
            tar = tarfile.open(import_path, 'r:gz')
            fc_start = datetime.now()
            files_in_tar = sum(1 for member in tar if member.isreg())
            fc_stop = datetime.now()
            print(f'{files_in_tar} files in archive. {fc_stop - fc_start}')
        except (OSError):
            print(f'Error opening {import_path}, not a tgz?')
            return

        # Iterate the files and import the games
        db = self.state.db_access
        tar_records = 0
        sgf_count = 0
        sgf_parse_error = 0
        sgf_added = 0
        sgf_duplicate = 0

        start_time = datetime.now()
        last_update = datetime.now()

        try:
            for tarinfo in tar:
                # TODO should I check tarfile.isreg() here too?
                tar_records += 1
                if tar_records % 500 == 0:
                    tnow = datetime.now()
                    print(f'   {tar_records} / {files_in_tar} ({(tar_records / files_in_tar) * 100:5.2f}%) [{tnow - last_update}]')
                    last_update = tnow
                _, extension = os.path.splitext(tarinfo.name)
                extension = extension.lower()
                if extension == '.sgf':
                    sgf_count += 1
                    reader = tar.extractfile(tarinfo)
                    sgf_data = reader.read().decode('utf-8') # TODO what encoding?
                    sgf = sgf_parser.SGFParser()
                    try:
                        sgf.import_from_sgf_file_text(sgf_data, tarinfo.name)
                    except sgf_parser.SGFParserException:
                        sgf_parse_error += 1
                        continue

                    try:
                        db.add_game_record(sgf)
                        sgf_added += 1
                    except DBAccessDuplicate:
                        sgf_duplicate += 1
                    except DBAccessGameRecordError:
                        sgf_parse_error += 1
                    except DBAccessException as e:
                        # This is a fatal error
                        print(f'   ! DB ERROR ! {e} : {tarinfo.name}')
                        return
        except EOFError as e:
            print(f'Error while reading {arg_path} - {e}')
            return

        stop_time = datetime.now()
        print(f'Elapsed Time: {stop_time - start_time}')
        print(f'Found {sgf_count} game records, added {sgf_added} games.')
        print(f'{sgf_duplicate} duplicates, {sgf_parse_error} parse errors')
