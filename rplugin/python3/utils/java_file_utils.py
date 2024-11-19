from pathlib import Path

from custom_types.log_level import LogLevel
from custom_types.create_java_file_args import CreateJavaFileArgs
from custom_types.java_file_type import JavaFileType
from utils.path_utils import PathUtils
from utils.common_utils import CommonUtils
from utils.treesitter_utils import TreesitterUtils
from utils.logging import Logging


class JavaFileLib:
    def __init__(
        self,
        nvim,
        logging: Logging,
        treesitter_utils: TreesitterUtils,
        path_utils: PathUtils,
        common_utils: CommonUtils,
    ):
        self.nvim = nvim
        self.logging = logging
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.common_utils = common_utils

    def get_boiler_plate(
        self,
        file_type: JavaFileType,
        package_path: str,
        file_name: str,
        debug: bool = False,
    ) -> bytes:
        boiler_plates = {
            "class": f"""package {package_path};\n\npublic class {file_name} {{\n\n}}""",
            "interface": f"""package {package_path};\n\npublic interface {file_name} {{\n\n}}""",
            "enum": f"""package {package_path};\n\npublic enum {file_name} {{\n\n}}""",
            "record": f"""package {package_path};\n\npublic record {file_name}(\n\n) {{}}""",
            "annotation": f"""package {package_path};\n\npublic @interface {file_name} {{\n\n}}""",
        }
        boiler_plate = boiler_plates.get(file_type.value, "")
        if debug:
            self.logging.log(
                f"Boiler plate: {boiler_plate}",
                LogLevel.DEBUG,
            )
        return boiler_plate.encode("utf-8")

    def get_file_path(
        self,
        package_path: str,
        file_name: str,
        debug: bool = False,
    ) -> Path:
        project_root_path = self.path_utils.get_project_root_path()
        main_class_path = self.path_utils.get_spring_main_class_path(project_root_path)
        base_path = self.common_utils.get_base_path(main_class_path)
        relative_path = self.common_utils.get_relative_path(package_path)
        file_path = self.common_utils.construct_file_path(
            base_path, relative_path, file_name
        )
        if debug:
            self.logging.log(
                [
                    f"Base path: {str(base_path)}",
                    f"Relative path: {str(relative_path)}",
                    f"File path: {str(file_path.parent)}",
                    f"Successfully created: {file_path}",
                ],
                LogLevel.DEBUG,
            )
        return file_path

    def create_java_file(
        self,
        args: CreateJavaFileArgs,
        debug: bool = False,
    ) -> None:
        boiler_plate = self.get_boiler_plate(
            args.file_type_enum, args.package_path, args.file_name, debug
        )
        file_path = self.get_file_path(args.package_path, args.file_name, debug)
        file_tree = self.treesitter_utils.convert_bytes_to_tree(boiler_plate)
        self.treesitter_utils.update_buffer(file_tree, file_path, True)
