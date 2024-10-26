from pathlib import Path
from typing import Dict, List, Literal, Tuple

from lib.treesitterlib import TreesitterLib
from util.logging import Logging


class PathLib:
    ROOT_FILES = [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle.kts",
        "settings.gradle",
    ]

    def __init__(self, cwd: Path, treesitter_lib: TreesitterLib, logging: Logging):
        self.cwd: Path = cwd
        self.logging: Logging = logging
        self.treesitter_lib: TreesitterLib = treesitter_lib
        self.spring_project_root_path: str = self.get_spring_project_root_path()
        self.spring_main_class_path: str = self.get_spring_main_class_path()
        self.spring_root_package_path: str = self.get_spring_root_package_path()

    def get_all_jpa_entities(self, debug: bool = False) -> Dict[str, Tuple[str, Path]]:
        root_path = Path(self.get_spring_project_root_path(debug))
        entities_found: Dict[str, Tuple[str, Path]] = {}
        for p in root_path.rglob("*.java"):
            if self.treesitter_lib.is_buffer_jpa_entity(p, debug):
                entity_path = p
                entity_node = self.treesitter_lib.get_node_from_path(p, debug)
                entity_package_path = self.get_buffer_package_path(entity_path)
                entity_name = self.treesitter_lib.get_buffer_class_name(
                    entity_node, debug
                )
                if entity_name:
                    entities_found[entity_name] = (entity_package_path, entity_path)
        if debug:
            self.logging.log(
                [f"{e[0]} - {str(e[1])}" for e in entities_found.items()], "debug"
            )
        return entities_found

    def get_all_files_by_declaration_type(
        self,
        declaration_type: Literal["class", "enum", "interface", "annotation", "record"],
        debug: bool = False,
    ):
        declaration_types = {
            "class": """
            (
                (class_declaration
                    name: (identifier) @class_name
                ) @class_decl
            )
            """,
            "enum": """
            (
                (enum_declaration
                    name: (identifier) @class_name
                ) @enum_decl
            )
            """,
            "interface": """
            (
                (interface_declaration
                    name: (identifier) @class_name
                ) @interface_decl
            )
            """,
            "annotation": """
            (
                (annotation_type_declaration
                    name: (identifier) @class_name
                ) @annotation_decl
            )
            """,
            "record": """
            (
                (record_declaration
                    name: (identifier) @class_name
                ) @record_decl
            )
            """,
        }
        root_path = Path(self.get_spring_project_root_path(debug))
        found_files: List[Tuple[str, str, Path]] = []
        for p in root_path.rglob("*.java"):
            node = self.treesitter_lib.get_node_from_path(p, debug)
            results = self.treesitter_lib.query_node(
                node, declaration_types[declaration_type], debug
            )
            get_next = False
            if len(results) > 1:
                for result in results:
                    node_text = self.treesitter_lib.get_node_text(result[0])
                    if get_next:
                        package_path = self.get_buffer_package_path(p, debug)
                        found_files.append((node_text, package_path, p))
                        break
                    if "public " + declaration_type in node_text:
                        get_next = True
        if debug:
            self.logging.log([x[0] for x in found_files], "debug")
        return found_files

    def get_buffer_package_path(
        self,
        buffer_path: Path,
        debug: bool = False,
    ) -> str:
        parent_path = buffer_path.parent
        index_to_replace: int
        try:
            index_to_replace = parent_path.parts.index("main")
        except ValueError:
            error_msg = "Unable to split parent path"
            self.logging.log(error_msg, "error")
            raise ValueError(error_msg)
        package_path = str(Path(*parent_path.parts[index_to_replace + 2 :])).replace(
            "/", "."
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer path: {str(buffer_path)}",
                    f"Index to replace: {index_to_replace}",
                    f"Parent path: {str(parent_path)}",
                    f"Package path: {package_path}",
                ],
                "debug",
            )
        return package_path

    def get_spring_project_root_path(self, debug: bool = False) -> str:
        cwd = Path(self.cwd)
        while cwd != cwd.root:
            if any((cwd / root_file).exists() for root_file in self.ROOT_FILES):
                if debug:
                    self.logging.log(f"Root path found: {str(cwd)}", "debug")
                return str(cwd.resolve())
            cwd = cwd.parent
        error_msg = "Root path not found"
        self.logging.log(
            error_msg,
            "error",
        )
        raise FileNotFoundError(error_msg)

    def get_spring_root_package_path(self, debug: bool = False) -> str:
        main_dir_name = "main"
        full_path = Path(self.spring_main_class_path)
        path_parts = Path(full_path).parts
        try:
            main_dir_index = path_parts.index(main_dir_name)
        except ValueError:
            error_msg = f"Couldn't find {main_dir_name} in the path"
            self.logging.log(
                error_msg,
                "error",
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
                "debug",
            )
        return package_path

    def get_spring_main_class_path(self, debug: bool = False) -> str:
        root_path = Path(self.spring_project_root_path)
        for p in root_path.rglob("*.java"):
            if self.treesitter_lib.is_buffer_main_class(p, debug):
                if debug:
                    self.logging.log(f"Main class path: {str(p.resolve())}", "debug")
                return str(p.resolve())
        error_msg = "Main class path not found"
        self.logging.log(
            error_msg,
            "error",
        )
        raise FileNotFoundError(error_msg)
