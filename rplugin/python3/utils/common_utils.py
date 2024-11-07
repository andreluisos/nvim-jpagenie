from re import sub
from typing import List, Optional

from tree_sitter import Tree
from custom_types.java_file_data import JavaFileData
from custom_types.declaration_type import DeclarationType
from custom_types.log_level import LogLevel
from utils.treesitter_utils import TreesitterUtils
from utils.path_utils import PathUtils
from pathlib import Path

from utils.logging import Logging


class CommonUtils:
    def __init__(
        self,
        cwd: Path,
        path_utils: PathUtils,
        treesitter_utils: TreesitterUtils,
        logging: Logging,
    ) -> None:
        self.cwd = cwd
        self.logging = logging
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.importings: List[str] = []

    def pluralize_word(self, word: str, debug: bool = False) -> str:
        pluralized_word: str
        if word.endswith(("s", "sh", "ch", "x", "z")):
            pluralized_word = word + "es"
        elif word.endswith("y") and word[-2] not in "aeiou":
            pluralized_word = word[:-1] + "ies"
        elif word.endswith("f"):
            pluralized_word = word[:-1] + "ves"
        elif word.endswith("fe"):
            pluralized_word = word[:-2] + "ves"
        else:
            pluralized_word = word + "s"
        if debug:
            self.logging.log(f"Pluralized word: {pluralized_word}", LogLevel.DEBUG)
        return pluralized_word

    def convert_to_snake_case(self, text: str, debug: bool = False) -> str:
        snaked_field_name = sub(r"(?<!^)(?=[A-Z])", "_", text).lower()
        if debug:
            self.logging.log(
                f"Snaked field name: {snaked_field_name}",
                LogLevel.DEBUG,
            )
        return snaked_field_name

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
            self.logging.log(error_msg, LogLevel.DEBUG)
            raise ValueError(error_msg)
        package_path = str(Path(*parent_path.parts[index_to_replace + 2 :])).replace(
            "/", "."
        )
        if debug:
            self.logging.log(
                [
                    f"Index to replace: {index_to_replace}",
                    f"Parent path: {str(parent_path)}",
                    f"Package path: {package_path}",
                ],
                LogLevel.DEBUG,
            )
        return package_path

    def get_java_file_data(
        self, file_path: Path, debug: bool = False
    ) -> Optional[JavaFileData]:
        file_tree = self.treesitter_utils.convert_buffer_to_tree(file_path)
        decl_type_query_param = """
        [
            (class_declaration) 
            (enum_declaration) 
            (annotation_type_declaration) 
            (interface_declaration) 
            (record_declaration)
        ] @decl_type 
        """
        query_result = self.treesitter_utils.query_match(
            file_tree, decl_type_query_param
        )
        for result in query_result:
            decl_name = result.child_by_field_name("name")
            if decl_name and decl_name.text and result.text:
                decl_name_str = self.treesitter_utils.convert_bytes_to_string(
                    decl_name.text
                )
                if decl_name_str == file_path.stem:
                    result_tree = self.treesitter_utils.convert_buffer_to_tree(
                        result.text
                    )
                    declaration_type: DeclarationType = DeclarationType.CLASS
                    is_jpa_entity = (
                        self.treesitter_utils.buffer_public_class_has_annotation(
                            tree=result_tree, annotation_name="Entity", debug=debug
                        )
                    )
                    if result.type == "class_declaration":
                        declaration_type = DeclarationType.CLASS
                    elif result.type == "enum_declaration":
                        declaration_type = DeclarationType.ENUM
                    elif result.type == "interface_declaration":
                        declaration_type = DeclarationType.INTERFACE
                    elif result.type == "annotation_declaration":
                        declaration_type = DeclarationType.ANNOTATION
                    else:
                        declaration_type = DeclarationType.RECORD
                    return JavaFileData(
                        file_name=decl_name_str,
                        package_path=self.get_buffer_package_path(
                            buffer_path=file_path, debug=debug
                        ),
                        path=file_path,
                        tree=file_tree,
                        declaration_type=declaration_type,
                        is_jpa_entity=is_jpa_entity,
                    )

    def get_all_java_files_data(self, debug: bool = False) -> List[JavaFileData]:
        root_path = self.path_utils.get_spring_project_root_path()
        files_found: List[JavaFileData] = []
        for p in root_path.rglob("*.java"):
            if "main" not in p.parts:
                continue
            file_data: Optional[JavaFileData] = self.get_java_file_data(p, debug)
            if file_data:
                files_found.append(file_data)
        if debug:
            self.logging.log(
                [
                    f"Root path: {str(root_path)}",
                    f"Files found:\n{[f.print() for f in files_found]}",
                ],
                LogLevel.DEBUG,
            )
        return files_found

    def add_to_importing_list(
        self, import_list: List[str], debug: bool = False
    ) -> None:
        imports_to_extend = []
        for i in import_list:
            if i not in self.importings:
                imports_to_extend.append(i)
        if debug:
            self.logging.log(
                [
                    f"Previous import list: {str(self.importings)}",
                    f"New imports: {str(imports_to_extend)}",
                    f"New import list: {str(self.importings + imports_to_extend)}",
                ],
                LogLevel.DEBUG,
            )
        self.importings.extend(imports_to_extend)

    def add_imports_to_file_tree(self, file_tree: Tree, debug: bool = False) -> Tree:
        package_query_param = "(package_declaration) @package_decl"
        query_results = self.treesitter_utils.query_match(
            tree=file_tree, query_param=package_query_param
        )
        if len(query_results) != 1:
            error_msg = "File package not defined or defined incorrectly"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        insert_byte: int = query_results[0].end_byte + 1
        import_list = [f"import {e};" for e in self.importings]
        merged_import_list = "\n".join(import_list)
        updated_tree = self.treesitter_utils.insert_code_at_position(
            merged_import_list, insert_byte, file_tree
        )
        if debug:
            self.logging.log(
                [
                    f"Package query param: {package_query_param}",
                    f"Query results len: {len(query_results)}",
                    f"Insert byte: {insert_byte}",
                    f"Merged import list: {merged_import_list}",
                    f"Updated tree: {updated_tree}",
                ],
                LogLevel.DEBUG,
            )
        self.importings = []
        return updated_tree
