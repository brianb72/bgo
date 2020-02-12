from attr import attrs, attrib
from attr import Factory as attr_factory
import game_of_go.game_of_go as game_of_go
import utils.go_board as go_board

DEFAULT_DATABASE_PATH = './database.sqlite'


@attrs
class ShellState:
    working_dir = attrib()
    database_path = attrib(default=DEFAULT_DATABASE_PATH)
    commands = attrib(default={})
    db_access = attrib(default=None)
    search_board = attrib(default=go_board.GoBoard())
    session = attrib(default=None)
    key_bindings = attrib(default=None)
