from pathlib import Path

from pynvim.api.nvim import Nvim
import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser
from messaging import Messaging
from constants.java_types import JAVA_TYPES


class TreesitterUtil:
    JAVA_LANGUAGE = Language(tsjava.language())
    PARSER = Parser(JAVA_LANGUAGE)
    JAVA_TYPES = JAVA_TYPES

    def __init__(self, nvim: Nvim, cwd: Path, messaging: Messaging):
        self.nvim = nvim
        self.cwd: Path = cwd
        self.messaging = messaging
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

    def reload_format_organize_buffer(self, buffer_path: Path) -> None:
        self.nvim.command(f"e {str(buffer_path)}")
        self.nvim.command("lua vim.lsp.buf.format({ async = true })")
        self.nvim.command("lua require('jdtls').organize_imports()")

    def is_buffer_jpa_entity(self, buffer_path: Path, debugger: bool = False) -> bool:
        buffer_node = self.get_node_from_path(buffer_path)
        results = self.query_node(
            buffer_node, self.class_annotation_query, debugger=debugger
        )
        buffer_is_entity = self.query_results_has_term(
            results, "Entity", debugger=debugger
        )
        if debugger:
            self.messaging.log(f"buffer path: {str(buffer_path)}", "debug")
        if not buffer_is_entity:
            if debugger:
                self.messaging.log("buffer is jpa entity", "debug")
            return False
        if debugger:
            self.messaging.log("buffer is not jpa entity", "debug")
        return True

    def get_buffer_from_path(self, buffer_path: Path, debugger: bool = False) -> bytes:
        if debugger:
            self.messaging.log(f"Buffer path: {str(buffer_path)}", "debug")
        return buffer_path.read_text(encoding="utf-8").encode("utf-8")

    def get_node_from_path(self, buffer_path: Path, debugger: bool = False) -> Node:
        if debugger:
            self.messaging.log(f"Buffer path: {str(buffer_path)}", "debug")
        buffer = self.get_buffer_from_path(buffer_path, debugger=debugger)
        return self.PARSER.parse(buffer).root_node

    def get_node_text(self, node: Node, debugger: bool = False) -> str:
        node_text = node.text.decode("utf-8") if node.text is not None else ""
        if debugger:
            self.messaging.log(f"Returned node text: {node_text}", "debug")
        return node_text

    def query_node(
        self, node: Node, query: str, debugger: bool = False
    ) -> list[tuple[Node, str]]:
        if debugger:
            self.messaging.log(f"Query: {query}", "debug")
        _query = self.JAVA_LANGUAGE.query(query)
        results = _query.captures(node)
        if debugger:
            self.messaging.log(f"Returned {len(results)} entries.", "debug")
        return results

    def query_results_has_term(
        self,
        query_results: list[tuple[Node, str]],
        search_term: str,
        debugger: bool = False,
    ) -> bool:
        def iterate_nodes(node: Node) -> bool:
            node_text = self.get_node_text(node, debugger=debugger)
            if node_text == search_term:
                if debugger:
                    self.messaging.log(
                        f"Search term '{search_term}' found in node with text '{node_text}'.",
                        "debug",
                    )
                return True
            for child in node.children:
                if iterate_nodes(child):
                    return True
            return False

        if debugger:
            self.messaging.log(f"Search term: {search_term}", "debug")
        for result in query_results:
            if iterate_nodes(result[0]):
                return True
        if debugger:
            self.messaging.log("Search term is not present.", "debug")
        return False

    def get_node_class_name(self, node: Node, debugger: bool = False) -> str | None:
        class_name_query = """
        (class_declaration
            name: (identifier) @class_name
            )
        """
        results = self.query_node(node, class_name_query)
        if debugger:
            self.messaging.log(f"Found {len(results)} entries.", "debug")
        if len(results) == 1:
            class_name = self.get_node_text(results[0][0])
            if debugger:
                self.messaging.log(f"Class name: {class_name}", "debug")
            return class_name
        self.messaging.log("No class name found", "debug")
        return None

    def insert_code_into_position(
        self, code: str, insert_position, buffer_path: Path, debugger: bool = False
    ) -> None:
        buffer_bytes = self.get_buffer_from_path(buffer_path)
        code_bytes = code.encode("utf-8")
        new_source = (
            buffer_bytes[:insert_position] + code_bytes + buffer_bytes[insert_position:]
        )
        if debugger:
            self.messaging.log(f"Buffer: {str(buffer_path)}", "debug")
            self.messaging.log(f"Code: {code}", "debug")
            self.messaging.log(f"Insert position: {insert_position}", "debug")
        buffer_path.write_bytes(new_source)

    def get_field_type_import_path(
        self, field_type: str, debugger: bool = False
    ) -> str | None:
        for type_tuple in JAVA_TYPES:
            if field_type == type_tuple[0]:
                import_path: str
                if type_tuple[1] is not None:
                    import_path = f"{type_tuple[1]}.{type_tuple[0]}"
                else:
                    # For primitive types or when value is None
                    import_path = field_type[0]
                if debugger:
                    self.messaging.log(f"Import path: {import_path}", "debug")
                return import_path
        if debugger:
            self.messaging.log("Field type not found", "debug")
        return None

    def insert_import_path_into_buffer(
        self, buffer_path: Path, import_path: str, debugger: bool = False
    ) -> None:
        buffer_node = self.get_node_from_path(buffer_path, debugger)
        insert_position: int
        import_declarations = self.query_node(
            buffer_node, self.import_declarations_query, debugger
        )
        if len(import_declarations) > 0:
            insert_position = import_declarations[len(import_declarations) - 1][
                0
            ].end_byte
        else:
            class_declaration = self.query_node(
                buffer_node, self.class_declaration_query, debugger
            )
            if len(class_declaration) != 1:
                error_msg = "Unable to query class declaration"
                self.messaging.log(error_msg, "error")
                raise ValueError(error_msg)
            insert_position = class_declaration[0][0].start_byte
        import_path_bytes = f"\n\n{import_path}\n\n".encode("utf-8")
        template = f"import {import_path_bytes};"
        self.insert_code_into_position(template, insert_position, buffer_path, debugger)
        self.nvim.command(f"e {str(buffer_path)}")
