from pathlib import Path

from pynvim.api.nvim import Nvim

from constants.java_basic_types import JAVA_BASIC_TYPES
from utils.entity_field_utils import EntityFieldUtils
from utils.javafilelib import JavaFileLib
from utils.jpa_repo_utils import JpaRepositoryUtils
from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils
from utils.entity_rel_utils import EntityRelationshipUtils
from utils.common_utils import CommonUtils
from utils.entity_creation_utils import EntityCreationUtils
from utils.file_utils import FileUtils
from utils.logging import Logging


class Base(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.ui_path = str(Path(__file__).parent.resolve().joinpath("ui"))
        self.file_utils = FileUtils()
        self.java_basic_types = JAVA_BASIC_TYPES
        self.logging = Logging(self.nvim)
        self.treesitter_utils = TreesitterUtils(
            self.nvim, self.java_basic_types, self.cwd, self.logging
        )
        self.path_utils = PathUtils(self.cwd, self.treesitter_utils, self.logging)
        self.java_file_utils = JavaFileLib(
            self.nvim, self.logging, self.treesitter_utils
        )
        self.jpa_repo_utils = JpaRepositoryUtils(
            self.nvim, self.treesitter_utils, self.path_utils, self.logging
        )
        self.common_utils = CommonUtils(
            self.nvim, self.cwd, self.treesitter_utils, self.path_utils, self.logging
        )
        self.entity_field_utils = EntityFieldUtils(
            self.nvim,
            self.java_basic_types,
            self.treesitter_utils,
            self.common_utils,
            self.logging,
        )
        self.entity_rel_utils = EntityRelationshipUtils(
            self.nvim,
            self.treesitter_utils,
            self.path_utils,
            self.common_utils,
            self.logging,
        )
        self.entity_creation_utils = EntityCreationUtils(
            self.nvim,
            self.treesitter_utils,
            self.path_utils,
            self.common_utils,
            self.logging,
        )
