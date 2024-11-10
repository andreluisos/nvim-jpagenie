from pathlib import Path
from typing import List, Optional
from pynvim.api.nvim import Nvim

from custom_types.entity_type import EntityType
from custom_types.log_level import LogLevel
from utils.treesitter_utils import TreesitterUtils
from utils.common_utils import CommonUtils
from utils.path_utils import PathUtils
from utils.logging import Logging


class EntityCreationUtils:
    def __init__(
        self,
        nvim: Nvim,
        treesitter_utils: TreesitterUtils,
        path_utils: PathUtils,
        common_utils: CommonUtils,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.logging = logging
        self.common_utils = common_utils

    def get_base_path(self, main_class_path: Path, debug: bool = False) -> Path:
        base_path = main_class_path.parent
        if debug:
            self.logging.log(f"Base path: {str(base_path)}", LogLevel.DEBUG)
        return base_path

    def get_relative_path(self, package_path: str, debug: bool = False) -> Path:
        relative_path = Path(package_path.replace(".", "/"))
        if debug:
            self.logging.log(f"Relative path: {str(relative_path)}", LogLevel.DEBUG)
        return relative_path

    def construct_file_path(
        self, base_path: Path, relative_path: Path, file_name: str, debug: bool = False
    ) -> Path:
        try:
            index_to_replace = base_path.parts.index("main")
        except ValueError:
            error_msg = "Unable to parse root directory"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        file_path = (
            Path(*base_path.parts[: index_to_replace + 2])
            / relative_path
            / f"{file_name}.java"
        )
        if debug:
            self.logging.log(f"File path: {str(file_path)}", LogLevel.DEBUG)
        return file_path

    def generate_new_entity_template(
        self,
        package_path: str,
        entity_name: str,
        entity_type: EntityType,
        parent_entity_type: Optional[str],
        parent_entity_package_path: Optional[str],
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = ["jakarta.persistence.Table"]
        snaked_entity_name = self.common_utils.convert_to_snake_case(entity_name, debug)
        if entity_name == "User":
            snaked_entity_name += "_"
        template = f"package {package_path};\n\n"
        if entity_type == "entity":
            imports_to_add.append("jakarta.persistence.Entity")
            template += "@Entity\n"
        elif entity_type == "embeddable":
            imports_to_add.append("jakarta.persistence.Embeddable")
            template += "@Embeddable\n"
        else:
            imports_to_add.append("jakarta.persistence.MappedSuperclass")
            template += "@MappedSuperclass\n"
        template += f'@Table(name = "{snaked_entity_name}")\n'
        if parent_entity_type and parent_entity_package_path:
            imports_to_add.append(parent_entity_package_path + "." + parent_entity_type)
            template += f"public class {entity_name} extends {parent_entity_type} {{}}"
        else:
            template += f"public class {entity_name} {{}}"
        if debug:
            self.logging.log(
                [
                    f"Snaked entity name: {snaked_entity_name}",
                    f"Template:\n{template}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return template

    def create_new_entity(
        self,
        package_path: str,
        entity_name: str,
        entity_type: EntityType,
        parent_entity_type: Optional[str],
        parent_entity_package_path: Optional[str],
        debug: bool = False,
    ):
        main_class_path = self.path_utils.get_spring_main_class_path()
        base_path = self.get_base_path(main_class_path)
        relative_path = self.get_relative_path(package_path)
        final_path = self.construct_file_path(
            base_path=base_path, relative_path=relative_path, file_name=entity_name
        )
        if final_path.exists():
            error_msg = f"File {str(final_path)} already exists"
            self.logging.log(error_msg, LogLevel.ERROR)
        template = self.generate_new_entity_template(
            package_path=package_path,
            entity_name=entity_name,
            entity_type=entity_type,
            parent_entity_type=parent_entity_type,
            parent_entity_package_path=parent_entity_package_path,
            debug=debug,
        )
        buffer_tree = self.treesitter_utils.convert_bytes_to_tree(template.encode())
        buffer_tree = self.treesitter_utils.add_imports_to_file_tree(buffer_tree, debug)
        self.treesitter_utils.update_buffer(
            tree=buffer_tree, buffer_path=final_path, save=True, debug=debug
        )
        if debug:
            self.logging.log(
                [
                    f"Main class path: {str(main_class_path)}",
                    f"Base path: {str(base_path)}",
                    f"Relative path: {str(relative_path)}",
                    f"Final path: {str(final_path)}",
                    f"Template:\n{template}",
                    f"Final file:\n{buffer_tree.root_node.__repr__()}",
                ],
                LogLevel.DEBUG,
            )
