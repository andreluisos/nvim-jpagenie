from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser
from messaging import Messaging


class TreesitterUtil:
    JAVA_LANGUAGE = Language(tsjava.language())
    PARSER = Parser(JAVA_LANGUAGE)

    def __init__(self, cwd: Path, messaging: Messaging):
        self.cwd: Path = cwd
        self.messaging = messaging

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
