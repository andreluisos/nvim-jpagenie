from pathlib import Path

from custom_types.log_level import LogLevel
from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging
from shutil import which


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

    def get_plugin_base_path(self) -> Path:
        return Path(__file__).parent.parent.resolve()

    def get_java_executable_path(self) -> Path:
        java_path = which("java")
        if java_path:
            return Path(java_path)
        error_msg = "Java executable not found in PATH"
        self.logging.log(error_msg, LogLevel.CRITICAL)
        raise FileNotFoundError("Java executable not found in PATH.")

    def get_project_root_path(self) -> Path:
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

    def get_java_project_main_class(self, project_root_path: Path) -> Path:
        query = """
        (method_declaration
            (modifiers) @mod
            type: (void_type)
            name: (identifier) @method-name
            parameters: (formal_parameters
                (formal_parameter
                    type: (array_type
                        (type_identifier) @param-type)
                    name: (identifier) @param-name)))
        (#eq? @mod "public static")
        (#eq? @method-name "main")
        (#eq? @param-type "String")
        (#eq? @param-name "args")
        """
        for p in project_root_path.rglob("*.java"):
            buffer_tree = self.treesitter_utils.convert_path_to_tree(p)
            query_results = self.treesitter_utils.query_match(buffer_tree, query)
            if len(query_results) >= 1:
                return p.resolve()
        error_msg = "Main class path not found"
        self.logging.log(error_msg, LogLevel.CRITICAL)
        raise FileNotFoundError(error_msg)

    def get_spring_main_class_path(self, spring_project_root_path: Path) -> Path:
        for p in spring_project_root_path.rglob("*.java"):
            buffer_tree = self.treesitter_utils.convert_path_to_tree(p)
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
        project_root_path = self.get_project_root_path()
        full_path = self.get_spring_main_class_path(project_root_path)
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
