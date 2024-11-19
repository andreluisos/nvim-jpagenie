from typing import List, Optional
from pynvim.api.nvim import Nvim

from custom_types.entity_type import EntityType
from custom_types.log_level import LogLevel
from custom_types.create_entity_args import CreateEntityArgs
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
        if entity_type == EntityType.ENTITY:
            imports_to_add.append("jakarta.persistence.Entity")
            template += "@Entity\n"
        elif entity_type == EntityType.EMBEDDABLE:
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
        args: CreateEntityArgs,
        debug: bool = False,
    ):
        project_root_path = self.path_utils.get_project_root_path()
        main_class_path = self.path_utils.get_spring_main_class_path(project_root_path)
        base_path = self.common_utils.get_base_path(main_class_path)
        relative_path = self.common_utils.get_relative_path(args.package_path)
        final_path = self.common_utils.construct_file_path(
            base_path=base_path, relative_path=relative_path, file_name=args.entity_name
        )
        if final_path.exists():
            error_msg = f"File {str(final_path)} already exists"
            self.logging.log(error_msg, LogLevel.ERROR)
        template = self.generate_new_entity_template(
            package_path=args.package_path,
            entity_name=args.entity_name,
            entity_type=args.entity_type_enum,
            parent_entity_type=args.parent_entity_type,
            parent_entity_package_path=args.parent_entity_package_path,
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
