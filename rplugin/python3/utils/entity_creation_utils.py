from pathlib import Path
from typing import List, Optional, Tuple
from pynvim.api.nvim import Nvim

from utils.treesitter_utils import TreesitterUtils
from utils.common_utils import CommonUtils
from utils.path_utils import PathUtils
from utils.data_types import EntityType
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
        self.importings: List[str] = []

    def fetch_entity_data(self, debug: bool = False):
        parent_query = """
        (
        (class_declaration
            (modifiers
            (marker_annotation
                name: (identifier) @annotation_name)
            )
            name: (identifier) @class_name)
        (#match? @annotation_name "^(Entity|Table|MappedSuperclass)$")
        )
        (
        (class_declaration
            (modifiers
            (annotation
                name: (identifier) @annotation_name))
            name: (identifier) @class_name)
        (#match? @annotation_name "^(Entity|Table|MappedSuperclass)$")
        )
        """
        root_path = Path(self.path_utils.get_spring_project_root_path(debug))
        parent_entities_found: List[Tuple[str, str, Path]] = []
        for p in root_path.rglob("*.java"):
            buffer_node = self.treesitter_utils.get_node_from_path(p, debug)
            parent_results = self.treesitter_utils.query_node(
                buffer_node, parent_query, debug
            )
            if len(parent_results) >= 1:
                entity_name = self.treesitter_utils.get_node_text(
                    parent_results[len(parent_results) - 1][0], debug
                )
                package_path = self.path_utils.get_buffer_package_path(p, debug)
                parent_entities_found.append((entity_name, package_path, p))
        self.logging.log(
            [str(r) for r in parent_entities_found],
            "debug",
        )
        return parent_entities_found

    def get_base_path(self, main_class_path: str) -> Path:
        base_path = Path(main_class_path).parent
        return base_path

    def get_relative_path(self, package_path: str) -> Path:
        relative_path = Path(package_path.replace(".", "/"))
        return relative_path

    def construct_file_path(
        self, base_path: Path, relative_path: Path, file_name: str
    ) -> Path:
        try:
            index_to_replace = base_path.parts.index("main")
        except ValueError:
            error_msg = "Unable to parse root directory"
            self.logging.log(error_msg, "debug")
            raise ValueError(error_msg)
        file_path = (
            Path(*base_path.parts[: index_to_replace + 2])
            / relative_path
            / f"{file_name}.java"
        )
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
        self.importings.append("jakarta.persistence.Table")
        snaked_entity_name = self.common_utils.generate_snaked_field_name(
            entity_name, debug
        )
        if entity_name == "User":
            snaked_entity_name += "_"
        template = f"package {package_path};\n\n"
        if entity_type == "entity":
            self.importings.append("jakarta.persistence.Entity")
            template += "@Entity\n"
        elif entity_type == "embeddable":
            self.importings.append("jakarta.persistence.Embeddable")
            template += "@Embeddable\n"
        else:
            self.importings.append("jakarta.persistence.MappedSuperclass")
            template += "@MappedSuperclass\n"
        template += f'@Table(name = "{snaked_entity_name}")\n'
        if parent_entity_type and parent_entity_package_path:
            self.importings.append(
                parent_entity_package_path + "." + parent_entity_type
            )
            template += f"public class {entity_name} extends {parent_entity_type} {{}}"
        else:
            template += f"public class {entity_name} {{}}"
        if debug:
            self.logging.log(
                [
                    f"Entity name: {entity_name}",
                    f"Entity type: {entity_type}",
                    f"Parent entity type: {parent_entity_type}",
                    f"Parent entity package path: {parent_entity_package_path}",
                    f"Template:\n{template}",
                ],
                "debug",
            )
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
        main_class_path = self.path_utils.get_spring_main_class_path(debug)
        base_path = self.get_base_path(main_class_path)
        relative_path = self.get_relative_path(package_path)
        final_path = self.construct_file_path(
            base_path=base_path, relative_path=relative_path, file_name=entity_name
        )
        if final_path.exists():
            error_msg = f"File {str(final_path)} already exists"
            self.logging.log(error_msg, "error")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.touch(exist_ok=True)
        template = self.generate_new_entity_template(
            package_path=package_path,
            entity_name=entity_name,
            entity_type=entity_type,
            parent_entity_type=parent_entity_type,
            parent_entity_package_path=parent_entity_package_path,
            debug=debug,
        )
        buffer_bytes = self.treesitter_utils.get_bytes_from_path(final_path, debug)
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            template, 0, buffer_bytes, debug
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes=buffer_bytes,
            buffer_path=final_path,
            save=False,
            format=True,
            organize_imports=True,
        )
