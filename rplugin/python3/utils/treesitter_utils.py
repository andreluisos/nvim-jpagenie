from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pynvim.api import Buffer
import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser, Query, Tree
from pynvim.api.nvim import Nvim
from custom_types.log_level import LogLevel
from utils.logging import Logging


class TreesitterUtils:
    def __init__(
        self,
        nvim: Nvim,
        java_basic_types: list[tuple],
        cwd: Path,
        logging: Logging,
    ):
        self.nvim = nvim
        self.cwd: Path = cwd
        self.java_basic_types = java_basic_types
        self.logging = logging
        self.ts_java = Language(tsjava.language())
        self.parser = Parser(self.ts_java)
        self.importings: List[str] = []

    def convert_bytes_to_string(self, bytes_value: bytes) -> str:
        try:
            return bytes_value.decode()
        except (UnicodeDecodeError, AttributeError) as e:
            error_msg = f"Error decoding bytes: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def convert_string_to_bytes(self, string_value: str) -> bytes:
        try:
            return string_value.encode()
        except (UnicodeEncodeError, AttributeError) as e:
            error_msg = f"Error enconding string: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def convert_bytes_to_tree(self, file_bytes: bytes) -> Tree:
        try:
            if not file_bytes:
                raise ValueError("Input bytes are empty")
            buffer_tree = self.parser.parse(file_bytes)
            return buffer_tree
        except ValueError as e:
            error_msg = f"Error parsing bytes: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while parsing bytes: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def convert_path_to_tree(self, file_path: Path) -> Tree:
        buffer_bytes: bytes
        try:
            buffer_bytes = file_path.read_bytes()
        except (OSError, FileNotFoundError) as e:
            error_msg = f"Error reading from file path {str(file_path)}: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)
        buffer_tree = self.parser.parse(buffer_bytes)
        return buffer_tree

    def convert_buffer_to_tree(self, buffer: Buffer) -> Tree:
        try:
            if not buffer:
                raise ValueError("Input buffer is empty")
            buffer_bytes = "\n".join(buffer[:]).encode("utf-8")
            return self.convert_bytes_to_tree(buffer_bytes)
        except ValueError as e:
            error_msg = f"Error with buffer: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error while converting buffer to tree: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def convert_node_to_tree(self, node: Node) -> Tree:
        if node.text:
            return self.convert_bytes_to_tree(node.text)
        else:
            error_msg = "Unable to convert node into tree"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def query_match(self, tree: Tree, query_param: str) -> List[Node]:
        try:
            query: Query = self.ts_java.query(query_param)
        except Exception as e:
            error_msg = f"Error creating query from query_param '{query_param}': {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)
        try:
            query_results: List[Tuple[int, Dict[str, List[Node]]]] = query.matches(
                tree.root_node
            )
            nodes: List[Node] = []
            for result in query_results:
                for item in result[1].values():
                    for node in item:
                        nodes.append(node)
            return nodes
        except Exception as e:
            error_msg = f"Error matching query in tree: {e}"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise RuntimeError(error_msg)

    def get_node_text_as_string(self, node: Node, debug: bool = False) -> Optional[str]:
        node_text_str: Optional[str] = None
        if node.text:
            node_text_str = self.convert_bytes_to_string(node.text)
        if debug:
            self.logging.log(f"Node text: {node_text_str}", LogLevel.DEBUG)
        return node_text_str

    def get_node_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        if node.type == type_name:
            return node
        for child in node.children:
            result = self.get_node_by_type(child, type_name)
            if result is not None:
                return result
        return None

    def update_buffer(
        self,
        tree: Tree,
        buffer_path: Path,
        save: bool = False,
        format: bool = False,
        organize_imports: bool = False,
        debug: bool = False,
    ):
        node_text = tree.root_node.text
        if not node_text:
            error_msg = "Root node doesn't have text"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.nvim.command(f"e {str(buffer_path)}")
        if tree.root_node.text:
            self.nvim.current.buffer[:] = tree.root_node.text.decode().split("\n")
        if save:
            self.nvim.command(f"w {str(buffer_path)}")
        if format and not save:
            self.nvim.command("lua vim.lsp.buf.format({ async = true })")
        if organize_imports:
            self.nvim.command("lua require('jdtls').organize_imports()")
        if debug:
            self.logging.log(
                [
                    f"Updated buffer: {node_text.decode()}",
                    f"Original buffer: {buffer_path.read_text('utf-8')}",
                ],
                LogLevel.DEBUG,
            )

    def get_buffer_public_class_node_from_query_results(
        self, query_results: List[Node], debug: bool = False
    ) -> Optional[Node]:
        public_class_node: Optional[Node] = None
        for node in query_results:
            for child_node in node.children:
                if child_node.type == "modifiers" and child_node.text:
                    modifiers_text_str = self.convert_bytes_to_string(
                        child_node.text
                    ).split("\n")
                    if "public" in modifiers_text_str:
                        public_class_node = node
        if debug:
            public_class_node_str: Optional[str] = None
            if public_class_node and public_class_node.text:
                self.convert_bytes_to_string(public_class_node.text)
            self.logging.log(
                f"Found public class node: {public_class_node_str}", LogLevel.DEBUG
            )
        return public_class_node

    def get_buffer_public_class_name(
        self, tree: Tree, debug: bool = False
    ) -> Optional[str]:
        public_class_name: Optional[str] = None
        query_param = "(class_declaration) @class_decl"
        query_results: List[Node] = self.query_match(tree=tree, query_param=query_param)
        public_class_node = self.get_buffer_public_class_node_from_query_results(
            query_results=query_results, debug=debug
        )
        if public_class_node:
            name_node = public_class_node.child_by_field_name("name")
            if name_node and name_node.text:
                public_class_name = self.convert_bytes_to_string(name_node.text)
        if debug:
            self.logging.log(
                [
                    f"Query param: {query_param}",
                    f"Total query results: {len(query_results)}",
                    f"Public class name: {public_class_name}",
                ],
                LogLevel.DEBUG,
            )
        return public_class_name

    def buffer_public_class_has_annotation(
        self, tree: Tree, annotation_name: str, debug: bool = False
    ) -> bool:
        public_class_has_annotation: bool = False
        query_param = "(class_declaration) @class_decl"
        query_results: List[Node] = self.query_match(tree=tree, query_param=query_param)
        public_class_node = self.get_buffer_public_class_node_from_query_results(
            query_results=query_results, debug=debug
        )
        if public_class_node:
            modifiers = self.get_node_by_type(public_class_node, "modifiers")
            if modifiers:
                for child in modifiers.children:
                    if child.type in ["marker_annotation", "annotation"]:
                        name_node = child.child_by_field_name("name")
                        if name_node and name_node.text:
                            if (
                                self.convert_bytes_to_string(name_node.text)
                                == annotation_name
                            ):
                                public_class_has_annotation = True
        if debug:
            self.logging.log(
                f"Annotation found: {public_class_has_annotation}", LogLevel.DEBUG
            )
        return public_class_has_annotation

    def buffer_public_class_has_method(
        self, tree: Tree, method_name: str, debug: bool = False
    ):
        public_class_has_method: bool = False
        query_param = "(class_declaration) @class_decl"
        query_results: List[Node] = self.query_match(tree=tree, query_param=query_param)
        public_class_node = self.get_buffer_public_class_node_from_query_results(
            query_results=query_results, debug=debug
        )
        if public_class_node:
            body = public_class_node.child_by_field_name("body")
            if body:
                for child in body.children:
                    if child.type == "method_declaration":
                        node_name = child.child_by_field_name("name")
                        if node_name and node_name.text:
                            node_name_str = self.convert_bytes_to_string(node_name.text)
                            if node_name_str == method_name:
                                public_class_has_method = True
        if debug:
            self.logging.log(
                f"Public class has method '{method_name}': {public_class_has_method}",
                LogLevel.DEBUG,
            )
        return public_class_has_method

    def insert_code_at_position(
        self, code: str, insert_position, file_tree: Tree
    ) -> Tree:
        updated_tree: Optional[Tree] = None
        code_bytes = code.encode("utf-8")
        node_text_bytes = file_tree.root_node.text
        if node_text_bytes:
            node_text_bytes = (
                node_text_bytes[:insert_position]
                + code_bytes
                + node_text_bytes[insert_position:]
            )
            updated_tree = self.convert_bytes_to_tree(node_text_bytes)
        if not updated_tree:
            error_msg = "Unable to update tree"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        return updated_tree

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
        query_results = self.query_match(
            tree=file_tree, query_param=package_query_param
        )
        if len(query_results) != 1:
            error_msg = "File package not defined or defined incorrectly"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        insert_byte: int = query_results[0].end_byte + 1
        import_list = [f"import {e};" for e in self.importings]
        merged_import_list = "\n".join(import_list)
        updated_tree = self.insert_code_at_position(
            merged_import_list, insert_byte, file_tree
        )
        if debug:
            self.logging.log(
                [
                    f"Package query param: {package_query_param}",
                    f"Query results len: {len(query_results)}",
                    f"Insert byte: {insert_byte}",
                    f"Merged import list: {merged_import_list}",
                    f"Node before: {self.get_node_text_as_string(file_tree.root_node)}",
                    f"Node after: {self.get_node_text_as_string(updated_tree.root_node)}",
                ],
                LogLevel.DEBUG,
            )
        self.importings = []
        return updated_tree
