from pathlib import Path

from pynvim.api.nvim import Nvim
from tree_sitter import Node

from lib.pathlib import PathLib
from lib.treesitterlib import TreesitterLib
from util.logging import Logging


class JpaRepositoryLib:
    def __init__(
        self,
        nvim: Nvim,
        treesitter_lib: TreesitterLib,
        path_lib: PathLib,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_lib = treesitter_lib
        self.path_lib = path_lib
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
        id_type_import_path = self.treesitter_lib.get_field_type_import_path(
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
            self.logging.log(f"Boiler plate: {boiler_plate}", "debug")
        return boiler_plate

    def check_if_id_field_exists(self, buffer_node: Node, debug: bool = False) -> bool:
        results = self.treesitter_lib.query_node(
            buffer_node, self.id_field_annotation_query, debug=debug
        )
        id_annotation_found = self.treesitter_lib.query_results_has_term(
            results, "Id", debug=debug
        )
        if not id_annotation_found:
            return False
        return True

    def get_superclass_query_node(
        self, buffer_node: Node, debug: bool = False
    ) -> Node | None:
        results = self.treesitter_lib.query_node(
            buffer_node, self.superclass_query, debug=debug
        )
        if len(results) == 0:
            return None
        return results[0][0]

    def find_superclass_file_node(
        self, root_path: Path, superclass_name: str, debug: bool = False
    ) -> Node | None:
        for p in root_path.rglob("*.java"):
            _node = self.treesitter_lib.get_node_from_path(p, debug=debug)
            _results = self.treesitter_lib.query_node(
                _node, self.class_name_query, debug=debug
            )
            if len(_results) == 0:
                continue
            class_name = self.treesitter_lib.get_node_text(_results[0][0], debug=debug)
            if class_name == superclass_name:
                return _node
        return None

    def find_id_field_type(self, buffer_node: Node, debug: bool = False) -> str | None:
        child_node = buffer_node.children
        for child in child_node:
            if child.type != "class_declaration":
                self.find_id_field_type(child)
            else:
                for c1 in child.children:
                    if c1.type == "class_body":
                        for c2 in c1.children:
                            if c2.type == "field_declaration":
                                id_field_found = False
                                for c3 in c2.children:
                                    # c3 = modifiers, type_identifer and variable_declarator
                                    if c3.type == "modifiers":
                                        for c4 in c3.children:
                                            if c4.type == "marker_annotation":
                                                for c5 in c4.children:
                                                    if c5.type == "identifier":
                                                        if (
                                                            self.treesitter_lib.get_node_text(
                                                                c5
                                                            )
                                                            == "Id"
                                                        ):
                                                            id_field_found = True
                                    if id_field_found and c3.type == "type_identifier":
                                        id_field_type = (
                                            self.treesitter_lib.get_node_text(c3)
                                        )
                                        if debug:
                                            self.logging.log(
                                                f"Id field type: {id_field_type}",
                                                "debug",
                                            )
                                        return self.treesitter_lib.get_node_text(c3)
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
        if debug:
            self.logging.log(f"Class name: {class_name}", "debug")
            self.logging.log(f"JPA repository path: {file_path}", "debug")
            self.logging.log(f"Boiler plate: {boiler_plate}", "debug")
        if not file_path.exists():
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
            if file_path.exists():
                if debug:
                    self.logging.log(
                        "Successfuly created JPA repository file.", "debug"
                    )
                self.nvim.command(f"edit {file_path}")
                # TODO: make sure jdtls is in plugin dependencies.
                self.nvim.command("lua require('jdtls').organize_imports()")
                return
        self.logging.log(
            "Unable to create JPA repository file.",
            "error",
        )
        return

    def create_jpa_entity_for_current_buffer(
        self, root_path: Path, debug: bool = False
    ) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        node = self.treesitter_lib.get_node_from_path(buffer_path, debug=debug)
        class_name = self.treesitter_lib.get_node_class_name(node, debug=debug)
        package_path = self.path_lib.get_buffer_package_path(buffer_path, debug=debug)
        if class_name is None:
            self.logging.log(
                "Couldn't find the class name for this buffer.",
                "error",
            )
            return
        if not self.treesitter_lib.is_buffer_jpa_entity(buffer_path):
            self.logging.log(
                "Current buffer isn't a JPA entity.",
                "error",
            )
            return
        if not self.check_if_id_field_exists(node, debug=debug):
            superclass_name_node = self.get_superclass_query_node(node, debug=debug)
            if not superclass_name_node:
                self.logging.log(
                    "No Id found for this entity and no superclass to look for it.",
                    "error",
                )
                return
            superclass_name = self.treesitter_lib.get_node_text(
                superclass_name_node, debug=debug
            )
            superclass_node = self.find_superclass_file_node(
                root_path, superclass_name, debug
            )
            if superclass_node is None:
                self.logging.log(
                    "Unable to locate the superclass buffer.",
                    "error",
                )
                return
            if not self.check_if_id_field_exists(superclass_node, debug=debug):
                # TODO: Keep checking for superclasses?
                self.logging.log(
                    "Unable to find the Id field on the superclass.",
                    "error",
                )
                return
            id_type = self.find_id_field_type(superclass_node, debug=debug)
            if id_type is None:
                self.logging.log(
                    "Unable to find get the Id field type on the superclass.",
                    "error",
                )
                return
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
