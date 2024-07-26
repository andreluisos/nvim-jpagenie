from glob import glob
from pathlib import Path
from typing import Literal

import tree_sitter_java as tsjava
from pynvim import plugin, command
from tree_sitter import Language, Node, Parser


@plugin
class Util(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.java_language = Language(tsjava.language())
        self.parser = Parser(self.java_language)
        self.root_files = [
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "settings.gradle.kts",
            "settings.gradle",
        ]

    def is_spring_main_application_class(
        self, node: Node, code: str, in_class_declaration: bool = False
    ) -> bool:
        if in_class_declaration and node.type == "marker_annotation":
            if code[node.start_byte : node.end_byte] == "@SpringBootApplication":
                return True
        for child in node.children:
            if child.type == "class_declaration":
                if self.is_spring_main_application_class(child, code, True):
                    return True
            else:
                if self.is_spring_main_application_class(
                    child, code, in_class_declaration
                ):
                    return True
        return False

    def get_root_package_path(self) -> str | None:
        full_path = self.get_spring_main_class_path()
        if full_path is None:
            return None
        java_index = Path(full_path).parts.index("java")
        package_path = ".".join(Path(full_path).parts[java_index + 1 : -1])
        return package_path

    def get_spring_project_root_path(self) -> str | None:
        root_dir = Path(self.nvim.funcs.getcwd()).resolve()
        self.nvim.command(f"echo '{root_dir}'")
        root_found = False
        for file in glob(root_dir.joinpath("*").as_posix()):
            if Path(file).name in self.root_files:
                root_found = True
                break
        if root_found:
            return str(root_dir)
        self.nvim.command("echo 'Root not found'")
        return None

    @command("Test", nargs=0)
    def get_spring_main_class_path(self) -> str | None:
        root_dir = self.get_spring_project_root_path()
        if root_dir is None:
            return None
        for p in Path(root_dir).rglob("*.java"):
            root = self.parser.parse(bytes(p.read_text(), "utf-8"))
            main_class_found = self.is_spring_main_application_class(
                root.root_node, p.read_text()
            )
            if main_class_found:
                return str(p.resolve())  # Ensure absolute path
        return None

    def create_java_file(
        self,
        package_path: str,
        name: str,
        type: Literal["class", "interface", "record", "enum", "annotation"],
    ) -> None:
        file_path = self.get_spring_main_class_path()
        if file_path is None:
            return
        boiler_plate: str = ""
        if type in ["class", "interface", "enum"]:
            boiler_plate: str = (
                f"""package {package_path};\n\npublic {type} {name} {{\n\n}}"""
            )
        elif type == "record":
            boiler_plate = (
                f"""package {package_path};\n\npublic interface {name}(\n\n) {{}}"""
            )
        else:
            boiler_plate = (
                f"""package {package_path};\n\npublic @interface {name} {{\n\n}}"""
            )
        base_path = Path(file_path).parent
        relative_path = Path(package_path.replace(".", "/"))
        file_path = (
            base_path
            / relative_path.relative_to(relative_path.parent.as_posix())
            / f"{name}.java"
        )
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
        else:
            self.nvim.command(f"echo 'File {file_path} already exist'")
