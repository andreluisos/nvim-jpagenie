from pathlib import Path
from typing import List, Optional

import tree_sitter_java as tsjava
from pynvim.api import Buffer
from pynvim.api.nvim import Nvim
from tree_sitter import Language, Node, Parser
from utils.logging import Logging


class TreesitterUtils:
    JAVA_LANGUAGE = Language(tsjava.language())
    PARSER = Parser(JAVA_LANGUAGE)

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
        self.all_field_declarations_query = "(field_declaration) @field"
        self.class_body_query = "(class_body) @body"
        self.class_declaration_query = "(class_declaration) @class"
        self.class_annotation_query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        self.import_declarations_query = "(import_declaration) @import"
        self.main_class_query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        ) 
        """

    def update_buffer(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        save: bool = False,
        format: bool = False,
        organize_imports: bool = False,
        debug: bool = False,
    ) -> None:
        buffer_path.write_bytes(buffer_bytes)
        self.nvim.command(f"e {str(buffer_path)}")
        if save:
            self.nvim.command(f"w {str(buffer_path)}")
        if organize_imports:
            self.nvim.command("lua require('jdtls').organize_imports()")
        if format and not save:
            self.nvim.command("lua vim.lsp.buf.format({ async = true })")
        if debug:
            self.logging.log(
                [
                    f"Buffer:\n{buffer_bytes.decode('utf-8')}",
                    f"Buffer path: {str(buffer_path)}",
                    f"Format: {format}",
                    f"Organize imports: {organize_imports}",
                ],
                "debug",
            )

    def is_buffer_main_class(self, buffer_path: Path, debug: bool = False) -> bool:
        buffer_node = self.get_node_from_path(buffer_path, debug)
        results = self.query_node(buffer_node, self.main_class_query, debug)
        is_main_class = self.query_results_has_term(
            results, "SpringBootApplication", debug
        )
        if debug:
            self.logging.log(
                f"{str(buffer_path)} is {'not ' if not is_main_class else ' '}the main class",
                "debug",
            )
        return is_main_class

    def is_buffer_jpa_entity(self, buffer_path: Path, debug: bool = False) -> bool:
        buffer_node = self.get_node_from_path(buffer_path, debug)
        results = self.query_node(buffer_node, self.class_annotation_query, debug=debug)
        buffer_is_entity = self.query_results_has_term(results, "Entity", debug=debug)
        if debug:
            self.logging.log(
                [
                    f"buffer path: {str(buffer_path)}",
                    f"Buffer is {'not ' if not buffer_is_entity else ' '}JPA entity",
                ],
                "debug",
            )
        return buffer_is_entity

    def buffer_has_method(
        self, buffer_path: Path, method_name: str, debug: bool = False
    ) -> bool:
        query = """
        (method_declaration
            name: (identifier) @method_name)
        """
        buffer_node = self.get_node_from_path(buffer_path, debug)
        results = self.query_node(buffer_node, query, debug)
        buffer_has_method = self.query_results_has_term(results, method_name, debug)
        if debug:
            self.logging.log(
                [
                    f"Buffer path: {str(buffer_path)}",
                    f"Method name: {method_name}",
                    f"Method found: {buffer_has_method}",
                ],
                "debug",
            )
        return buffer_has_method

    def get_bytes_from_path(self, buffer_path: Path, debug: bool = False) -> bytes:
        if debug:
            self.logging.log(f"Buffer path: {str(buffer_path)}", "debug")
        return buffer_path.read_text(encoding="utf-8").encode("utf-8")

    def get_node_from_path(self, buffer_path: Path, debug: bool = False) -> Node:
        if debug:
            self.logging.log(f"Buffer path: {str(buffer_path)}", "debug")
        buffer = self.get_bytes_from_path(buffer_path, debug=debug)
        return self.PARSER.parse(buffer).root_node

    def get_node_from_bytes(self, buffer_bytes: bytes, debug: bool = False) -> Node:
        if debug:
            self.logging.log(f"Buffer:\n {buffer_bytes.decode('utf-8')}", "debug")
        return self.PARSER.parse(buffer_bytes).root_node

    def get_bytes_from_buffer(self, buffer: Buffer, debug: bool = False) -> bytes:
        buffer_bytes = "\n".join(buffer[:]).encode("utf-8")
        if debug:
            self.logging.log(f"Buffer:\n{buffer_bytes.decode('utf-8')}", "debug")
        return buffer_bytes

    def get_node_text(self, node: Node, debug: bool = False) -> str:
        node_text = node.text.decode("utf-8") if node.text is not None else ""
        if debug:
            self.logging.log(f"Node text: {node_text}", "debug")
        return node_text

    def get_entity_field_insert_point(
        self, buffer_bytes: bytes, debug: bool = False
    ) -> int:
        buffer_node = self.get_node_from_bytes(buffer_bytes)
        field_declarations = self.query_node(
            buffer_node, self.all_field_declarations_query, debug
        )
        field_declarations_count = len(field_declarations)
        if field_declarations_count != 0:
            # != 0 means there are existing field declarations
            last_field: Node = field_declarations[field_declarations_count - 1][0]
            position = (last_field.start_byte, last_field.end_byte)
            if debug:
                self.logging.log(
                    f"field_declarations_count: {field_declarations_count}", "debug"
                )
                self.logging.log(f"position: {position}", "debug")
            return position[1]
        class_body = self.query_node(buffer_node, self.class_body_query, debug)
        if len(class_body) != 1:
            self.logging.log(
                "Couldn't find the class declaration.",
                "error",
            )
            raise ValueError("Couldn't find the class declaration.")
        position = (
            class_body[0][0].start_byte,
            class_body[0][0].end_byte,
        )
        if debug:
            self.logging.log(f"class body count: {len(class_body)}", "debug")
            self.logging.log(f"position: {position}", "debug")
        return position[0] + 1

    def query_node(
        self, node: Node, query: str, debug: bool = False
    ) -> list[tuple[Node, str]]:
        _query = self.JAVA_LANGUAGE.query(query)
        results = _query.captures(node)
        if debug:
            self.logging.log(
                [f"Query: {query}", f"Returned {len(results)} entries."], "debug"
            )
        return results

    def query_results_has_term(
        self,
        query_results: list[tuple[Node, str]],
        search_term: str,
        debug: bool = False,
    ) -> bool:
        def iterate_nodes(node: Node) -> bool:
            node_text = self.get_node_text(node, debug=debug)
            if node_text == search_term:
                if debug:
                    self.logging.log(
                        f"Search term '{search_term}' found in node with text '{node_text}'.",
                        "debug",
                    )
                return True
            for child in node.children:
                if iterate_nodes(child):
                    return True
            return False

        for result in query_results:
            if iterate_nodes(result[0]):
                return True
        if debug:
            self.logging.log(f"Search term {search_term} is not present.", "debug")
        return False

    def get_buffer_class_name(
        self,
        buffer: Node | Path | bytes,
        debug: bool = False,
    ) -> str | None:
        class_name_query = """
        (class_declaration
            name: (identifier) @class_name
            )
        """
        node: Optional[Node] = None
        if isinstance(buffer, Node):
            node = buffer
        if isinstance(buffer, Path):
            node = self.get_node_from_path(
                buffer,
            )
        if isinstance(buffer, bytes):
            node = self.get_node_from_bytes(buffer, debug)
        if node is None:
            error_msg = "Something went wrong"
            self.logging.log(error_msg, "error")
            raise ValueError(error_msg)
        results = self.query_node(node, class_name_query)
        if len(results) == 1:
            class_name = self.get_node_text(results[0][0])
            if debug:
                self.logging.log(
                    [f"Found {len(results)} entries.", f"Class name: {class_name}"],
                    "debug",
                )
            return class_name
        self.logging.log("No class name found", "debug")
        return None

    def get_field_type_import_path(
        self, field_type: str, debug: bool = False
    ) -> str | None:
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
                        "debug",
                    )
                return import_path
        if debug:
            self.logging.log(f"Field type {field_type} not found", "debug")
        return None

    def insert_code_into_position(
        self, code: str, insert_position, buffer_bytes: bytes, debug: bool = False
    ) -> bytes:
        code_bytes = code.encode("utf-8")
        new_source = (
            buffer_bytes[:insert_position] + code_bytes + buffer_bytes[insert_position:]
        )
        if debug:
            self.logging.log(
                [f"Code: {code}", f"Insert position: {insert_position}"], "debug"
            )
        return new_source

    def insert_import_paths_into_buffer(
        self, buffer_bytes: bytes, import_paths: List[str], debug: bool = False
    ) -> bytes:
        buffer_node = self.get_node_from_bytes(buffer_bytes)
        updated_buffer_bytes: bytes = buffer_bytes
        for import_path in import_paths:
            insert_position: int
            import_declarations = self.query_node(
                buffer_node, self.import_declarations_query, debug
            )
            if len(import_declarations) > 0:
                insert_position = import_declarations[len(import_declarations) - 1][
                    0
                ].end_byte
            else:
                class_declaration = self.query_node(
                    buffer_node, self.class_declaration_query, debug
                )
                if len(class_declaration) != 1:
                    error_msg = "Unable to query class declaration"
                    self.logging.log(error_msg, "error")
                    raise ValueError(error_msg)
                insert_position = class_declaration[0][0].start_byte
            template = f"\nimport {import_path};\n"
            updated_buffer_bytes = self.insert_code_into_position(
                template, insert_position, updated_buffer_bytes, debug
            )
        return updated_buffer_bytes
