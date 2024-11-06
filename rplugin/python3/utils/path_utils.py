from pathlib import Path

from custom_types.log_level import LogLevel
from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging


class PathUtils:
    def __init__(self, cwd: Path, treesitter_utils: TreesitterUtils, logging: Logging):
        self.cwd: Path = cwd
        self.logging: Logging = logging
        self.treesitter_utils: TreesitterUtils = treesitter_utils
        self.root_files = [
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle.kts",
            "settings.gradle",
        ]

    def get_spring_project_root_path(self) -> Path:
        cwd = Path(self.cwd)
        while cwd != cwd.root:
            if any((cwd / root_file).exists() for root_file in self.root_files):
                return Path(cwd.resolve())
            cwd = cwd.parent
        error_msg = "Root path not found"
        self.logging.log(
            error_msg,
            LogLevel.CRITICAL,
        )
        raise FileNotFoundError(error_msg)

    def get_spring_main_class_path(self) -> Path:
        root_path = self.get_spring_project_root_path()
        for p in root_path.rglob("*.java"):
            buffer_tree = self.treesitter_utils.convert_buffer_to_tree(p)
            buffer_is_main_class = (
                self.treesitter_utils.buffer_public_class_has_annotation(
                    buffer_tree, "SpringBootApplication", False
                )
            )
            if buffer_is_main_class:
                return p.resolve()
        error_msg = "Main class path not found"
        self.logging.log(
            error_msg,
            LogLevel.CRITICAL,
        )
        raise FileNotFoundError(error_msg)

    def get_spring_root_package_path(self, debug: bool = False) -> str:
        main_dir_name = "main"
        full_path = self.get_spring_main_class_path()
        path_parts = Path(full_path).parts
        try:
            main_dir_index = path_parts.index(main_dir_name)
        except ValueError:
            error_msg = f"Couldn't find {main_dir_name} in the path"
            self.logging.log(
                error_msg,
                LogLevel.CRITICAL,
            )
            raise ValueError(error_msg)
        package_path = ".".join(path_parts[main_dir_index + 2 : -1])
        if debug:
            self.logging.log(
                [
                    f"main dir name: {main_dir_name}",
                    f"full path: {str(full_path)}",
                    f"package path: {package_path}",
                ],
                LogLevel.CRITICAL,
            )
        return package_path
