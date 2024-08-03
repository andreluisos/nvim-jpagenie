from pathlib import Path

from messaging import Messaging
from tsutil import TreesitterUtil


class PathUtil:
    ROOT_FILES = [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle.kts",
        "settings.gradle",
    ]

    def __init__(self, cwd: Path, tsutil: TreesitterUtil, messaging: Messaging):
        self.cwd: Path = cwd
        self.messaging: Messaging = messaging
        self.tsutil: TreesitterUtil = tsutil
        self.spring_project_root_path: str | None = self.get_spring_project_root_path()
        self.spring_main_class_path: str | None = self.get_spring_main_class_path()
        self.spring_root_package_path: str | None = self.get_spring_root_package_path()

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
            node = self.tsutil.get_node_from_path(p)
            results = self.tsutil.query_node(node, query)
            if self.tsutil.query_results_has_term(
                results, "SpringBootApplication", debugger=debugger
            ):
                if debugger:
                    self.messaging.log("Main class path found.", "debug")
                return str(p.resolve())
        self.messaging.log("Main class path not found.", "error", send_msg=True)
        raise FileNotFoundError("Main class path not found.")
