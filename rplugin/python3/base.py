from pathlib import Path

from pynvim.api.nvim import Nvim
from pynvim.plugin import plugin

from constants.typing import JAVA_BASIC_TYPES
from lib.entityfieldlib import EntityFieldLib
from lib.javafilelib import JavaFileLib
from lib.jparepolib import JpaRepositoryLib
from lib.pathlib import PathLib
from lib.treesitterlib import TreesitterLib
from util.argvalidator import ArgValidator
from util.logging import Logging


@plugin
class Base(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.java_basic_types = JAVA_BASIC_TYPES
        self.logging = Logging()
        self.arg_validator = ArgValidator(self.java_basic_types, self.logging)
        self.treesitter_lib = TreesitterLib(
            self.nvim, self.java_basic_types, self.cwd, self.logging
        )
        self.path_lib = PathLib(self.cwd, self.treesitter_lib, self.logging)
        self.java_file_lib = JavaFileLib(self.nvim, self.logging)
        self.jpa_repo_lib = JpaRepositoryLib(
            self.nvim, self.treesitter_lib, self.path_lib, self.logging
        )
        self.entity_field_lib = EntityFieldLib(
            self.nvim, self.java_basic_types, self.treesitter_lib, self.logging
        )
