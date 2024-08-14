from pathlib import Path
from typing import Literal

from util.logging import Logging


class JavaFileLib:
    def __init__(self, nvim, logging: Logging):
        self.nvim = nvim
        self.logging = logging

    def get_boiler_plate(
        self, file_type: str, package_path: str, file_name: str, debug: bool = False
    ) -> str:
        boiler_plate: str = ""
        if file_type in ["class", "interface", "enum"]:
            boiler_plate = f"""package {package_path};\n\npublic {file_type} {file_name} {{\n\n}}"""
        elif file_type == "record":
            boiler_plate = (
                f"""package {package_path};\n\npublic record {file_name}(\n\n) {{}}"""
            )
        else:
            boiler_plate = (
                f"""package {package_path};\n\npublic @interface {file_name} {{\n\n}}"""
            )
        if debug:
            self.logging.log(f"Boiler plate: {boiler_plate}", "debug")
        return boiler_plate

    def get_file_path(
        self,
        main_class_path: str,
        package_path: str,
        file_name: str,
        debug: bool = False,
    ) -> Path:
        base_path = Path(main_class_path).parent
        relative_path = Path(package_path.replace(".", "/"))
        index_to_replace: int
        try:
            index_to_replace = base_path.parts.index("main")
        except ValueError:
            self.logging.log("Unable to parse root directory.", "error")
            raise ValueError("Unable to parse root directory")
        file_path = (
            Path(*base_path.parts[: index_to_replace + 2])
            / relative_path
            / f"{file_name}.java"
        )
        if debug:
            self.logging.log(f"Base path: {str(base_path)}", "debug")
            self.logging.log(f"Relative path: {str(relative_path)}", "debug")
            self.logging.log(f"File path: {str(file_path.parent)}", "debug")
            self.logging.log(f"Successfully created: {file_path}", "debug")
        return file_path

    def create_java_file(
        self,
        main_class_path: str,
        package_path: str,
        file_name: str,
        file_type: Literal["class", "interface", "record", "enum", "annotation"],
        debug: bool = False,
    ) -> None:
        boiler_plate = self.get_boiler_plate(file_type, package_path, file_name, debug)
        file_path = self.get_file_path(main_class_path, package_path, file_name, debug)
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
        else:
            self.logging.log(
                f"Failed to create file {file_path} because it already exists", "error"
            )
            return
        self.nvim.command(f"edit {file_path}")
