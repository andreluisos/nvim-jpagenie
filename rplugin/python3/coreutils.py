from pathlib import Path
from typing import Literal

import tree_sitter_java as tsjava
from pynvim import plugin
from tree_sitter import Language, Node, Parser


@plugin
class Util(object):
    JAVA_LANGUAGE = Language(tsjava.language())
    PARSER = Parser(JAVA_LANGUAGE)
    ROOT_FILES = [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle.kts",
        "settings.gradle",
    ]

    def __init__(self, nvim):
        self.nvim = nvim
        self.spring_project_root_path: str | None = self.get_spring_project_root_path()
        self.spring_main_class_path: str | None = self.get_spring_main_class_path()
        self.spring_root_package_path: str | None = self.get_spring_root_package_path()
        if (
            self.spring_root_package_path is None
            or self.spring_project_root_path is None
            or self.spring_main_class_path is None
        ):
            self.nvim.command("echo 'Make sure this is a Spring Boot project.'")

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

    def get_spring_project_root_path(self) -> str | None:
        root_dir = Path(self.nvim.funcs.getcwd()).resolve()
        for file in root_dir.iterdir():
            if file.name in self.ROOT_FILES:
                self.nvim.command(f"echo '{root_dir.as_posix()}'")
                return root_dir.as_posix()
        self.nvim.command(
            "echo 'Root not found. Make sure this is a Spring Boot project.'"
        )

    def get_spring_root_package_path(self) -> str | None:
        full_path = self.spring_main_class_path
        if full_path is None:
            return None
        java_index = Path(full_path).parts.index("java")
        package_path = ".".join(Path(full_path).parts[java_index + 1 : -1])
        self.nvim.command(f"echo '{package_path}'")
        return package_path

    def get_spring_main_class_path(self) -> str | None:
        root_dir = self.spring_project_root_path
        if root_dir is None:
            return
        root_path = Path(root_dir)
        for p in root_path.rglob("*.java"):
            file_content = p.read_text(encoding="utf-8")
            root = self.PARSER.parse(file_content.encode("utf-8"))
            if self.is_spring_main_application_class(root.root_node, file_content):
                self.nvim.command(f"echo '{p.resolve().as_posix()}'")
                return p.resolve().as_posix()
        self.nvim.command(
            "echo 'Main class not found. Make sure this is a Spring Boot project.'"
        )

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
