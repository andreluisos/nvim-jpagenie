from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser
from messaging import Messaging


class Util:
    JAVA_LANGUAGE = Language(tsjava.language())
    PARSER = Parser(JAVA_LANGUAGE)
    ROOT_FILES = [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle.kts",
        "settings.gradle",
    ]

    def __init__(self, cwd: Path, messaging: Messaging):
        self.cwd: Path = cwd
        self.messaging = messaging
        self.spring_project_root_path: str | None = self.get_spring_project_root_path()
        self.spring_main_class_path: str | None = self.get_spring_main_class_path()
        self.spring_root_package_path: str | None = self.get_spring_root_package_path()

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

    def get_spring_project_root_path(self, debugger: bool = False) -> str | None:
        cwd = Path(self.cwd)
        if debugger:
            self.messaging.log(f"cwd: {cwd}", "debug")
        for file in cwd.iterdir():
            if file.name in self.ROOT_FILES:
                if debugger:
                    self.messaging.log(f"Root path found: {cwd}", "debug")
                return str(cwd.resolve())
        self.messaging.log("Root path not found.", "error", send_msg=True)
        return

    def get_spring_root_package_path(self, debugger: bool = False) -> str | None:
        full_path = self.spring_main_class_path
        if full_path is None:
            return None
        main_dir_index = Path(full_path).parts.index("main")
        package_path = ".".join(Path(full_path).parts[main_dir_index + 2 : -1])
        if debugger:
            self.messaging.log(f"Package path: {package_path}", "debug")
        return package_path

    def get_spring_main_class_path(self, debugger: bool = False) -> str | None:
        root_dir = self.spring_project_root_path
        query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        ) 
        """
        if root_dir is None:
            return
        root_path = Path(root_dir)
        for p in root_path.rglob("*.java"):
            if debugger:
                self.messaging.log(f"Checking file: {p.resolve()}", "debug")
            node = self.get_node_from_path(p)
            results = self.query_node(node, query)
            if self.query_results_has_term(
                results, "SpringBootApplication", debugger=debugger
            ):
                if debugger:
                    self.messaging.log("Main class path found.", "debug")
                return str(p.resolve())
        self.messaging.log("Main class path not found.", "error", send_msg=True)
        return
