from pathlib import Path
from typing import Literal

from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging


class JavaFileLib:
    def __init__(self, nvim, logging: Logging, treesitter_utils: TreesitterUtils):
        self.nvim = nvim
        self.logging = logging
        self.treesitter_utils = treesitter_utils

    def get_boiler_plate(
        self, file_type: str, package_path: str, file_name: str, debug: bool = False
    ) -> bytes:
        boiler_plates = {
            "class": f"""package {package_path};\n\npublic class {file_name} {{\n\n}}""",
            "interface": f"""package {package_path};\n\npublic interface {file_name} {{\n\n}}""",
            "enum": f"""package {package_path};\n\npublic enum {file_name} {{\n\n}}""",
            "record": f"""package {package_path};\n\npublic record {file_name}(\n\n) {{}}""",
            "annotation": f"""package {package_path};\n\npublic @interface {file_name} {{\n\n}}""",
        }
        boiler_plate = boiler_plates.get(file_type, "")
        if debug:
            self.logging.log(
                [
                    f"File type: {file_type}",
                    f"Package path: {package_path}",
                    f"File name: {file_name}",
                    f"Boiler plate: {boiler_plate}",
                ],
                "debug",
            )
        return boiler_plate.encode("utf-8")

    def get_base_path(self, main_class_path: str) -> Path:
        base_path = Path(main_class_path).parent
        return base_path

    def get_relative_path(self, package_path: str) -> Path:
        relative_path = Path(package_path.replace(".", "/"))
        return relative_path

    def construct_file_path(
        self, base_path: Path, relative_path: Path, file_name: str
    ) -> Path:
        try:
            index_to_replace = base_path.parts.index("main")
        except ValueError:
            error_msg = "Unable to parse root directory"
            self.logging.log(error_msg, "debug")
            raise ValueError(error_msg)
        file_path = (
            Path(*base_path.parts[: index_to_replace + 2])
            / relative_path
            / f"{file_name}.java"
        )
        return file_path

    def get_file_path(
        self,
        main_class_path: str,
        package_path: str,
        file_name: str,
        debug: bool = False,
    ) -> Path:
        base_path = self.get_base_path(main_class_path)
        relative_path = self.get_relative_path(package_path)
        file_path = self.construct_file_path(base_path, relative_path, file_name)
        if debug:
            self.logging.log(
                [
                    f"Base path: {str(base_path)}",
                    f"Relative path: {str(relative_path)}",
                    f"File path: {str(file_path.parent)}",
                    f"Successfully created: {file_path}",
                ],
                "debug",
            )
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
        self.treesitter_utils.update_buffer(boiler_plate, file_path, False, True, True)
