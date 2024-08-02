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

    def get_buffer_package_path(
        self,
        buffer_path: Path,
        debugger: bool = False,
    ) -> str:
        parent_path = buffer_path.parent
        if debugger:
            self.messaging.log(f"Buffer path: {str(buffer_path)}", "debug")
        index_to_replace: int
        try:
            index_to_replace = parent_path.parts.index("main")
        except ValueError:
            self.messaging.log("Unable to split parent path.", "error")
            raise ValueError("Unable to split parent path")
        if debugger:
            self.messaging.log(f"Index to replace: {index_to_replace}", "debug")
        package_path = str(Path(*parent_path.parts[index_to_replace + 2 :])).replace(
            "/", "."
        )
        if debugger:
            self.messaging.log(f"Parent path: {str(parent_path)}", "debug")
            self.messaging.log(f"Package path: {package_path}", "debug")
        return package_path

    def get_spring_project_root_path(self, debugger: bool = False) -> str:
        cwd = Path(self.cwd)
        if debugger:
            self.messaging.log(f"Starting directory: {cwd}", "debug")
        while cwd != cwd.root:
            if any((cwd / root_file).exists() for root_file in self.ROOT_FILES):
                if debugger:
                    self.messaging.log(f"Root path found: {cwd}", "debug")
                return str(cwd.resolve())
            cwd = cwd.parent
        self.messaging.log("Root path not found.", "error", send_msg=True)
        raise FileNotFoundError("Root path not found.")

    def get_spring_root_package_path(self, debugger: bool = False) -> str:
        full_path = self.spring_main_class_path
        if full_path is None:
            self.messaging.log(
                "Spring main class path is not set.", "error", send_msg=True
            )
            raise ValueError("Spring main class path is not set.")
        path_parts = Path(full_path).parts
        try:
            main_dir_index = path_parts.index("main")
        except ValueError:
            self.messaging.log(
                "Could not find 'main' in the path.", "error", send_msg=True
            )
            raise ValueError("Could not find 'main' in the path.")
        package_path = ".".join(path_parts[main_dir_index + 2 : -1])
        if debugger:
            self.messaging.log(f"Package path: {package_path}", "debug")
        return package_path

    def get_spring_main_class_path(self, debugger: bool = False) -> str:
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
            self.messaging.log(
                "Spring project root path is not set.", "error", send_msg=True
            )
            raise ValueError("Spring project root path is not set.")
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
        raise FileNotFoundError("Main class path not found.")
