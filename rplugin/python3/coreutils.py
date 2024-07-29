from pathlib import Path

from pynvim.api.nvim import walk
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

    def get_buffer_from_path(self, buffer_path: Path, debugger: bool = False) -> bytes:
        """This method will get the file content and read it as bytes.

        Args:
            buffer_path: the buffer path
            debugger: whether if logging is enabled for the method

        Returns:
            The content of the file in bytes.
        """
        if debugger:
            debug(f"method: {self.get_buffer_from_path.__name__}")
            debug(f"buffer path: {str(buffer_path)}")
        return buffer_path.read_text(encoding="utf-8").encode("utf-8")

    def get_node_from_path(self, buffer_path: Path, debugger: bool = False) -> Node:
        """This method will convert the buffer into a tree-sitter Node object.

        Args:
            buffer_path: the buffer path
            debugger: whether if logging is enabled for the method

        Returns:
            A tree-sitter's Node object.
        """
        if debugger:
            debug(f"method: {self.get_node_from_path.__name__}")
            debug(f"buffer path: {str(buffer_path)}")
        buffer = self.get_buffer_from_path(buffer_path, debugger=debugger)
        return self.PARSER.parse(buffer).root_node

    def get_node_text(self, node: Node, debugger: bool = False) -> str:
        """This method will get the text from a tree-sitter Node object.

        Args:
            node: the node used to get text coordinates
            debugger: whether if logging is enabled for the method

        Returns:
            String containing the text of the node.
        """
        if debugger:
            debug(f"method: {self.get_node_text.__name__}")
        node_text = node.text.decode("utf-8") if node.text is not None else ""
        if debugger:
            debug(f"node text: {node_text}")
        return node_text

    def query_node(
        self, node: Node, query: str, debugger: bool = False
    ) -> list[tuple[Node, str]]:
        """This method will query a tree-sitter Node object and capture the results.

        Args:
            node: the node the be queried
            query: the query itself
            debugger: whether if logging is enabled for the method

        Returns:
            A list of tuples containing the Node and it's name.
        """
        if debugger:
            debug(f"method: {self.query_node.__name__}")
            debug(f"query: {query}")
        _query = self.JAVA_LANGUAGE.query(query)
        results = _query.captures(node)
        if debugger:
            debug(f"Returned {len(results)} entries.")
        return results

    def query_results_has_term(
        self,
        query_results: list[tuple[Node, str]],
        search_term: str,
        debugger: bool = False,
    ) -> bool:
        """This method will iterate over a tree-sitter Node object query capture and
        search a specific term.
        Args:
            buffer_path: a Path object of the buffer
            query_results: the list of tuples containing the query results
            search_term: the search term as string
            debugger: whether if logging is enabled for the method

        Returns:
            True if the term was found in the query results.
        """

        def iterate_nodes(node: Node):
            """Recursively iterate over the node and its children to search for the term."""
            node_text = self.get_node_text(node, debugger=debugger)
            if node_text == search_term:
                if debugger:
                    debug(
                        f"Search term '{search_term}' found in node with text '{node_text}'."
                    )
                return True
            for child in node.children:
                if iterate_nodes(child):
                    return True
            return False

        if debugger:
            debug(f"method: {self.query_results_has_term.__name__}")
            debug(f"search term: {search_term}")
        for result in query_results:
            if iterate_nodes(result[0]):
                return True
        if debugger:
            debug("Search term is not present.")
        return False

    def buffer_has_class_annotation(
        self, buffer_path: Path, class_annotation: str, debugger: bool = False
    ) -> bool:
        """THis method will check if a buffer is a class and if it has an specific annotation.

        Args:
            buffer_path: the buffer path
            class_annotation: the class annotation object of the search
            debugger: whether if logging is enabled for the method

        Returns:
            True if present.
        """
        if debugger:
            debug(f"method: {self.buffer_has_class_annotation.__name__}")
            debug(f"buffer path: {buffer_path}")
            debug(f"class annotation: {class_annotation}")
        node = self.get_node_from_path(buffer_path, debugger=debugger)
        query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        ) 
        """
        results = self.query_node(node, query)
        if self.query_results_has_term(results, class_annotation, debugger=debugger):
            debug("Class annotation found")
            return True
        debug("Class annotation not found")
        return False

    def get_spring_project_root_path(self, debugger: bool = False) -> str | None:
        """This method will check for the ROOT_FILES in every directory, starting from
        the current working directory.
        Args:
            debugger: whether if logging is enabled for the method

        Returns:
            Absolute path of the project root directory.
        """
        cwd = Path(self.cwd)
        if debugger:
            debug(f"method: {self.get_spring_project_root_path.__name__}")
            debug(f"cwd: {cwd}")
        for file in cwd.iterdir():
            if file.name in self.ROOT_FILES:
                if debugger:
                    debug(f"Root path found: {cwd}")
                return str(cwd.resolve())
        if debugger:
            debug("Root path not found.")

    def get_spring_root_package_path(self, debugger: bool = False) -> str | None:
        """This method builds the root package path, generally used when creating classes.

        Args:
            debugger: whether if logging is enabled for the method

        Returns:
            The absolute path of the package root directory.
        """
        if debugger:
            debug(f"method: {self.get_spring_root_package_path.__name__}")
        full_path = self.spring_main_class_path
        if full_path is None:
            return None
        main_dir_index = Path(full_path).parts.index("main")
        package_path = ".".join(Path(full_path).parts[main_dir_index + 2 : -1])
        if debugger:
            debug(f"package path: {package_path}")
        return package_path

    def get_spring_main_class_path(self, debugger: bool = False) -> str | None:
        """This method searches for the class with @SpringBootApplication annotation.

        Args:
            debugger: whether if logging is enabled for the method

        Returns:
            The absolute path of the class with @SpringBootApplication annotation.
        """
        if debugger:
            debug(f"method: {self.get_spring_main_class_path.__name__}")
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
                debug(f"Checking file: {p.resolve()}")
            node = self.get_node_from_path(p)
            results = self.query_node(node, query)
            if self.query_results_has_term(
                results, "SpringBootApplication", debugger=debugger
            ):
                if debugger:
                    debug("Main class path found.")
                return str(p.resolve())
        if debugger:
            debug("Main class path not found.")
        return
