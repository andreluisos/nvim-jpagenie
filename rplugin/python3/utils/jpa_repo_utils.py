from pathlib import Path
from typing import Optional

from pynvim.api.nvim import Nvim
from tree_sitter import Tree

from custom_types.log_level import LogLevel
from custom_types.declaration_type import DeclarationType
from utils.common_utils import CommonUtils
from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging


class JpaRepositoryUtils:
    def __init__(
        self,
        nvim: Nvim,
        java_basic_types: list[tuple],
        common_utils: CommonUtils,
        treesitter_utils: TreesitterUtils,
        path_utils: PathUtils,
        logging: Logging,
    ):
        self.nvim = nvim
        self.java_basic_types = java_basic_types
        self.common_utils = common_utils
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.logging = logging

    def get_basic_field_type_import_path(
        self, field_type: str, debug: bool = False
    ) -> Optional[str]:
        for type_tuple in self.java_basic_types:
            if field_type == type_tuple[0]:
                import_path: str = ""
                if type_tuple[1] is not None:
                    import_path = f"{type_tuple[1]}.{type_tuple[0]}"
                else:
                    # For primitive types or when value is None
                    import_path = field_type[0]
                if debug:
                    self.logging.log(
                        [f"Field type: {field_type}", f"Import path: {import_path}"],
                        LogLevel.DEBUG,
                    )
                return import_path
        if debug:
            self.logging.log(f"Field type {field_type} not found", LogLevel.DEBUG)

    def generate_jpa_repository_template(
        self, class_name: str, package_path: str, id_type: str, debug: bool = False
    ) -> Tree:
        id_type_import_path = self.get_basic_field_type_import_path(id_type, debug)
        boiler_plate = (
            f"package {package_path};\n\n"
            f"import org.springframework.data.jpa.repository.JpaRepository;\n\n"
        )
        if id_type_import_path:
            boiler_plate += f"import {id_type_import_path};\n\n"
        boiler_plate += (
            f"public interface {class_name}Repository "
            f"extends JpaRepository<{class_name}, {id_type}> {{}}"
        )
        if debug:
            self.logging.log(
                f"Boiler plate:\n{boiler_plate}",
                LogLevel.DEBUG,
            )
        return self.treesitter_utils.convert_buffer_to_tree(boiler_plate.encode())

    def check_if_id_field_exists(self, file_tree: Tree, debug: bool = False) -> bool:
        id_field_annotation_query = """
        (modifiers
            (marker_annotation
                name: (identifier) @annotation_name
            )
        )
        """
        query_results = self.treesitter_utils.query_match(
            file_tree, id_field_annotation_query
        )
        id_annotation_found = False
        for result in query_results:
            if result.text and result.text.decode() == "Id":
                id_annotation_found = True
        if debug:
            self.logging.log(
                f"ID annotation found: {id_annotation_found}",
                LogLevel.DEBUG,
            )
        return id_annotation_found

    def get_superclass_name(
        self, file_tree: Tree, debug: bool = False
    ) -> Optional[str]:
        superclass_name: Optional[str] = None
        class_declaration_query = "(class_declaration) @class_decl"
        super_class_query = """
        (class_declaration
            superclass: (superclass
                (type_identifier) @superclass_type))
        """
        query_results = self.treesitter_utils.query_match(
            file_tree, class_declaration_query
        )
        main_class_node = (
            self.treesitter_utils.get_buffer_public_class_node_from_query_results(
                query_results, debug
            )
        )
        if main_class_node:
            main_class_tree = self.treesitter_utils.convert_node_to_tree(
                main_class_node
            )
            query_results = self.treesitter_utils.query_match(
                main_class_tree, super_class_query
            )
            if len(query_results) != 1:
                return None
            if query_results[0].text:
                superclass_name = query_results[0].text.decode()
        if debug:
            self.logging.log(
                f"Superclass name: {superclass_name}",
                LogLevel.DEBUG,
            )
        return superclass_name

    def find_superclass_file_tree(
        self, superclass_name: str, debug: bool = False
    ) -> Optional[Tree]:
        class_name_query = """
        (class_declaration
            name: (identifier) @class_name
            )
        """
        root_path = self.path_utils.get_spring_project_root_path()
        super_class_tree: Optional[Tree] = None
        for p in root_path.rglob("*.java"):
            file_tree = self.treesitter_utils.convert_buffer_to_tree(p)
            query_results = self.treesitter_utils.query_match(
                file_tree, class_name_query
            )
            if len(query_results) == 0:
                continue
            for result in query_results:
                if result.text and result.text.decode() == superclass_name:
                    return file_tree
        if debug:
            self.logging.log(
                [
                    f"Query param: {class_name_query}",
                    f"Found superclass tree: {super_class_tree.__repr__() if super_class_tree else None}",
                ],
                LogLevel.DEBUG,
            )
        return super_class_tree

    def find_id_field_type(self, file_tree: Tree, debug: bool = False) -> Optional[str]:
        field_marker_name_query = """
        (field_declaration
            (modifiers
                (marker_annotation) @marker_annotation))
        """
        query_results = self.treesitter_utils.query_match(
            file_tree, field_marker_name_query
        )
        if len(query_results) != 1:
            return None
        id_field_type: Optional[str] = None
        modifiers = query_results[0].parent
        if modifiers and modifiers.parent:
            field_declaration = modifiers.parent.child_by_field_name("type")
            if field_declaration and field_declaration.text:
                id_field_type = field_declaration.text.decode()
        if debug:
            self.logging.log(f"Id field type: {id_field_type}", LogLevel.DEBUG)
        return id_field_type

    def create_jpa_repository(self, buffer_path: Path, debug: bool = False) -> None:
        file_data = self.common_utils.get_java_file_data(buffer_path, debug)
        if file_data is None:
            error_msg = "Couldn't get file data"
            self.logging.log(
                error_msg,
                LogLevel.DEBUG,
            )
            raise ValueError(error_msg)
        if (
            not file_data.is_jpa_entity
            or file_data.declaration_type != DeclarationType.CLASS
        ):
            error_msg = "Invalid JPA Entity"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        if not self.check_if_id_field_exists(file_data.tree, debug=debug):
            error_msg = "Unable to get superclass data"
            superclass_name = self.get_superclass_name(file_data.tree)
            if not superclass_name:
                self.logging.log(error_msg, LogLevel.ERROR)
                raise ValueError(error_msg)
            superclass_tree = self.find_superclass_file_tree(superclass_name, debug)
            if superclass_tree is None:
                self.logging.log(
                    error_msg,
                    LogLevel.ERROR,
                )
                raise ValueError(error_msg)
            if not self.check_if_id_field_exists(superclass_tree, debug=debug):
                # TODO: Keep checking for superclasses?
                error_msg = "Unable to find the Id field on the superclass"
                self.logging.log(
                    error_msg,
                    LogLevel.ERROR,
                )
                raise ValueError(error_msg)
            id_type = self.find_id_field_type(superclass_tree, debug=debug)
            if id_type is None:
                error_msg = "Unable to find get the Id field type on the superclass"
                self.logging.log(
                    error_msg,
                    LogLevel.ERROR,
                )
                raise ValueError(error_msg)
            jpa_repo_tree = self.generate_jpa_repository_template(
                class_name=file_data.file_name,
                package_path=file_data.package_path,
                id_type=id_type,
                debug=debug,
            )
            jpa_repo_path = buffer_path.parent.joinpath(
                f"{file_data.file_name}Repository.java"
            )
            self.treesitter_utils.update_buffer(
                tree=jpa_repo_tree,
                buffer_path=jpa_repo_path,
                save=False,
                format=True,
                organize_imports=True,
                debug=True,
            )
            if debug:
                self.logging.log(
                    f"JPA Repository tree:\n{jpa_repo_tree.__repr__()}\n",
                    LogLevel.DEBUG,
                )
