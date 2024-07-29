from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser
from logging import basicConfig, debug, DEBUG

basicConfig(filename="coreutils.log", level=DEBUG)


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

    def __init__(self, cwd: Path):
        self.cwd: Path = cwd
        self.spring_project_root_path: str | None = self.get_spring_project_root_path()
        self.spring_main_class_path: str | None = self.get_spring_main_class_path()
        self.spring_root_package_path: str | None = self.get_spring_root_package_path()

    def get_node_text(self, node: Node, buffer: bytes, debugger: bool = False) -> str:
        if debugger:
            debug(f"method: {self.get_node_text.__name__}")
        node_text = buffer[node.start_byte : node.end_byte].decode("utf-8")
        if debugger:
            debug(f"node text: {node_text}")
        return node_text

    def query_buffer(
        self, buffer: bytes, query: str, debugger: bool = False
    ) -> list[tuple[Node, str]]:
        if debugger:
            debug(f"method: {self.query_buffer.__name__}")
            debug(f"query: {query}")
        _query = self.JAVA_LANGUAGE.query(query)
        node = self.PARSER.parse(buffer).root_node
        return _query.captures(node)

    def is_search_term_in_query_results(
        self,
        buffer: bytes,
        query_results: list[tuple[Node, str]],
        search_term: str,
        debugger: bool = False,
    ) -> bool:
        if debugger:
            debug(f"method: {self.is_search_term_in_query_results.__name__}")
            debug(f"search term: {search_term}")
        for result in query_results:
            node_text = self.get_node_text(result[0], buffer)
            if node_text == search_term:
                if debugger:
                    debug("Search term is present.")
                return True
        if debugger:
            debug("Search term is not present.")
        return False

    def is_class_annotation_present(
        self,
        node: Node,
        code: bytes,
        annotation: str,
        in_class_declaration: bool = False,
    ) -> bool:
        if node.type == "marker_annotation":
            annotation_text = code[node.start_byte : node.end_byte].decode("utf-8")
            if annotation_text == annotation:
                return True
        elif node.type == "class_declaration":
            in_class_declaration = True
        for child in node.children:
            if self.is_class_annotation_present(
                child, code, annotation, in_class_declaration
            ):
                return True
        return False

    def is_buffer_jpa_entity(self, buffer: Path) -> bool:
        file_content = buffer.read_text(encoding="utf-8").encode("utf-8")
        root = self.PARSER.parse(file_content)
        if self.is_class_annotation_present(root.root_node, file_content, "@Entity"):
            return True
        return False

    def get_spring_project_root_path(self) -> str | None:
        root_dir = Path(self.cwd)
        for file in root_dir.iterdir():
            if file.name in self.ROOT_FILES:
                return root_dir.as_posix()

    def get_spring_root_package_path(self) -> str | None:
        full_path = self.spring_main_class_path
        if full_path is None:
            return None
        java_index = Path(full_path).parts.index("java")
        package_path = ".".join(Path(full_path).parts[java_index + 1 : -1])
        return package_path

    def get_spring_main_class_path(self) -> str | None:
        root_dir = self.spring_project_root_path
        if root_dir is None:
            return
        root_path = Path(root_dir)
        for p in root_path.rglob("*.java"):
            file_content = p.read_text(encoding="utf-8").encode("utf-8")
            root = self.PARSER.parse(file_content)
            if self.is_class_annotation_present(
                root.root_node, file_content, "@SpringBootApplication"
            ):
                return p.resolve().as_posix()
