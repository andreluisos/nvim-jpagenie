from pathlib import Path

from pynvim.api.nvim import Nvim

from constants.java_basic_types import JAVA_BASIC_TYPES
from utils.gradle_helper import GradleHelper
from utils.java_file_utils import JavaFileLib
from utils.common_utils import CommonUtils
from utils.entity_creation_utils import EntityCreationUtils
from utils.entity_field_utils import EntityFieldUtils
from utils.entity_rel_utils import EntityRelationshipUtils
from utils.jpa_repo_utils import JpaRepositoryUtils
from utils.logging import Logging
from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils


class Base(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.ui_path = str(Path(__file__).parent.resolve().joinpath("ui"))
        self.logging = Logging(self.nvim)
        self.java_basic_types = JAVA_BASIC_TYPES
        self.treesitter_utils = TreesitterUtils(
            nvim=self.nvim,
            java_basic_types=self.java_basic_types,
            cwd=self.cwd,
            logging=self.logging,
        )
        self.path_utils = PathUtils(
            cwd=self.cwd, treesitter_utils=self.treesitter_utils, logging=self.logging
        )
        self.common_utils = CommonUtils(
            cwd=self.cwd,
            path_utils=self.path_utils,
            treesitter_utils=self.treesitter_utils,
            logging=self.logging,
        )
        self.entity_creation_utils = EntityCreationUtils(
            nvim=self.nvim,
            treesitter_utils=self.treesitter_utils,
            path_utils=self.path_utils,
            common_utils=self.common_utils,
            logging=self.logging,
        )
        self.jpa_repo_utils = JpaRepositoryUtils(
            nvim=self.nvim,
            java_basic_types=self.java_basic_types,
            common_utils=self.common_utils,
            treesitter_utils=self.treesitter_utils,
            path_utils=self.path_utils,
            logging=self.logging,
        )
        self.entity_field_utils = EntityFieldUtils(
            nvim=self.nvim,
            java_basic_types=self.java_basic_types,
            treesitter_utils=self.treesitter_utils,
            common_utils=self.common_utils,
            logging=self.logging,
        )
        self.entity_relationship_utils = EntityRelationshipUtils(
            nvim=self.nvim,
            treesitter_utils=self.treesitter_utils,
            path_utils=self.path_utils,
            common_utils=self.common_utils,
            logging=self.logging,
        )
        self.java_file_utils = JavaFileLib(
            nvim=self.nvim,
            logging=self.logging,
            treesitter_utils=self.treesitter_utils,
            path_utils=self.path_utils,
            common_utils=self.common_utils,
        )
        self.gradle_helper = GradleHelper(
            nvim=self.nvim,
            cwd=self.cwd,
            path_utils=self.path_utils,
            treesitter_utils=self.treesitter_utils,
            common_utils=self.common_utils,
            logging=self.logging,
        )
