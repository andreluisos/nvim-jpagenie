from pathlib import Path

from pynvim.api.nvim import Nvim
from tree_sitter import Node

from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging


class JpaRepositoryUtils:
    def __init__(
        self,
        nvim: Nvim,
        treesitter_utils: TreesitterUtils,
        path_utils: PathUtils,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.logging = logging
        self.field_declaration_query = """
        (field_declaration
            (modifiers
                (annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        self.id_field_annotation_query = """
        (modifiers
            (marker_annotation
                name: (identifier) @annotation_name
            )
        )
        """
        self.superclass_query = """
        (superclass
            (type_identifier) @superclass_name
         )
        """
        self.class_name_query = """
        (class_declaration
            name: (identifier) @class_name
            )
        """

    def generate_jpa_repository_template(
        self, class_name: str, package_path: str, id_type: str, debug: bool = False
    ) -> str:
        id_type_import_path = self.treesitter_utils.get_field_type_import_path(
            id_type, debug
        )
        boiler_plate = (
            f"package {package_path};\n\n"
            f"import org.springframework.data.jpa.repository.JpaRepository;\n\n"
        )
        if id_type_import_path:
            boiler_plate += f"import {id_type_import_path};\n\n"
        boiler_plate += f"public interface {class_name}Repository extends JpaRepository<{class_name}, {id_type}> {{}}"
        if debug:
            self.logging.log(
                [
                    f"Class name: {class_name}",
                    f"Package path: {package_path}",
                    f"Id type: {id_type}",
                    f"Boiler plate:\n{boiler_plate}",
                ],
                "debug",
            )
        return boiler_plate

    def check_if_id_field_exists(self, buffer_node: Node, debug: bool = False) -> bool:
        results = self.treesitter_utils.query_node(
            buffer_node, self.id_field_annotation_query, debug=debug
        )
        id_annotation_found = self.treesitter_utils.query_results_has_term(
            results, "Id", debug=debug
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer node: {buffer_node}",
                    f"ID annotation found: {id_annotation_found}",
                ],
                "debug",
            )
        return id_annotation_found

    def get_superclass_query_node(
        self, buffer_node: Node, debug: bool = False
    ) -> Node | None:
        results = self.treesitter_utils.query_node(
            buffer_node, self.superclass_query, debug=debug
        )
        if debug:
            self.logging.log(
                [
                    f"Buffer node: {buffer_node}",
                    f"Superclass query results: {results}",
                ],
                "debug",
            )
        if len(results) == 0:
            return None
        return results[0][0]

    def find_superclass_file_node(
        self, root_path: Path, superclass_name: str, debug: bool = False
    ) -> Node | None:
        for p in root_path.rglob("*.java"):
            node = self.treesitter_utils.get_node_from_path(p, debug=debug)
            results = self.treesitter_utils.query_node(
                node, self.class_name_query, debug=debug
            )
            if debug:
                self.logging.log(
                    [
                        f"File path: {p}",
                        f"Node: {node}",
                        f"Query results: {results}",
                    ],
                    "debug",
                )
            if len(results) == 0:
                continue
            class_name = self.treesitter_utils.get_node_text(
                results[0][0], debug=debug
            )
            if debug:
                self.logging.log(
                    [
                        f"Class name: {class_name}",
                    ],
                    "debug",
                )
            if class_name == superclass_name:
                return node
        return None

    def find_id_field_type(self, buffer_node: Node, debug: bool = False) -> str | None:
        child_nodes = buffer_node.children
        for child in child_nodes:
            if child.type != "class_declaration":
                self.find_id_field_type(child)
                continue
            for class_body in child.children:
                if class_body.type != "class_body":
                    continue
                for field_declaration in class_body.children:
                    if field_declaration.type != "field_declaration":
                        continue
                    id_field_found = False
                    for field_component in field_declaration.children:
                        if field_component.type == "modifiers":
                            for modifier in field_component.children:
                                if modifier.type == "marker_annotation":
                                    for identifier in modifier.children:
                                        if identifier.type == "identifier":
                                            if (
                                                self.treesitter_utils.get_node_text(
                                                    identifier
                                                )
                                                == "Id"
                                            ):
                                                id_field_found = True
                                                if debug:
                                                    self.logging.log(
                                                        "Id field found",
                                                        "debug",
                                                    )
                        if id_field_found and field_component.type == "type_identifier":
                            id_field_type = self.treesitter_utils.get_node_text(
                                field_component
                            )
                            if debug:
                                self.logging.log(
                                    f"Id field type: {id_field_type}",
                                    "debug",
                                )
                            return id_field_type
        if debug:
            self.logging.log("Id field type not found", "debug")
        return None

    def create_jpa_repository_file(
        self,
        buffer_path: Path,
        class_name: str,
        boiler_plate: str,
        debug: bool = False,
    ) -> None:
        file_path = buffer_path.parent.joinpath(f"{class_name}Repository.java")
        self.treesitter_utils.update_buffer(
            boiler_plate.encode("utf-8"), file_path, False, True, True
        )
        if debug:
            self.logging.log(
                [
                    f"Class name: {class_name}",
                    f"JPA repository path: {file_path}",
                    f"Boiler plate: {boiler_plate}",
                ],
                "debug",
            )

    def create_jpa_entity_for_current_buffer(
        self, root_path: Path, debug: bool = False
    ) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        node = self.treesitter_utils.get_node_from_path(buffer_path, debug=debug)
        class_name = self.treesitter_utils.get_buffer_class_name(node, debug=debug)
        package_path = self.path_utils.get_buffer_package_path(
            buffer_path, debug=debug
        )
        if class_name is None:
            error_msg = "Couldn't find the class name for this buffer"
            self.logging.log(
                error_msg,
                "error",
            )
            raise FileNotFoundError(error_msg)
        if not self.treesitter_utils.is_buffer_jpa_entity(buffer_path):
            error_msg = "Current buffer isn't a JPA entity"
            self.logging.log(
                error_msg,
                "error",
            )
            raise ValueError(error_msg)
        if not self.check_if_id_field_exists(node, debug=debug):
            superclass_name_node = self.get_superclass_query_node(node, debug=debug)
            if not superclass_name_node:
                error_msg = (
                    "No Id found for this entity and no superclass to look for it"
                )
                self.logging.log(
                    error_msg,
                    "error",
                )
                raise ValueError(error_msg)
            superclass_name = self.treesitter_utils.get_node_text(
                superclass_name_node, debug=debug
            )
            superclass_node = self.find_superclass_file_node(
                root_path, superclass_name, debug
            )
            if superclass_node is None:
                error_msg = "Unable to locate the superclass buffer"
                self.logging.log(
                    error_msg,
                    "error",
                )
                raise ValueError(error_msg)
            if not self.check_if_id_field_exists(superclass_node, debug=debug):
                # TODO: Keep checking for superclasses?
                error_msg = "Unable to find the Id field on the superclass"
                self.logging.log(
                    error_msg,
                    "error",
                )
                raise ValueError(error_msg)
            id_type = self.find_id_field_type(superclass_node, debug=debug)
            if id_type is None:
                error_msg = "Unable to find get the Id field type on the superclass"
                self.logging.log(
                    error_msg,
                    "error",
                )
                raise ValueError(error_msg)
            boiler_plate = self.generate_jpa_repository_template(
                class_name=class_name,
                package_path=package_path,
                id_type=id_type,
                debug=debug,
            )
            self.create_jpa_repository_file(
                buffer_path=buffer_path,
                class_name=class_name,
                boiler_plate=boiler_plate,
                debug=debug,
            )
