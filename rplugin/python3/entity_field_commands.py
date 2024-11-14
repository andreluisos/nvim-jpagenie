from pathlib import Path
from typing import Dict, List, Literal, Optional

from pynvim import plugin, command, function

from pynvim.api import Nvim
from tree_sitter import Tree

from base import Base
from custom_types.declaration_type import DeclarationType
from custom_types.log_level import LogLevel
from custom_types.java_file_data import JavaFileData
from custom_types.create_id_field_args import CreateIdEntityFieldArgs
from custom_types.create_basic_field_args import CreateBasicEntityFieldArgs
from custom_types.create_enum_field_args import CreateEnumEntityFieldArgs


@plugin
class EntityFieldCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.all_java_files: List[JavaFileData] = []
        self.data: List[Dict[str, str]] = []
        self.buffer_file_data: Optional[JavaFileData] = None
        self.ui_file: Literal["basic_field.lua", "id_field.lua", "enum_field.lua"]
        self.debug: bool = False

    def process_command_args(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        self.logging.log(args, LogLevel.DEBUG)
        if len(args) < 1 or len(args) > 2:
            error_msg = "At least one and max 2 arguments allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        self.all_java_files = self.common_utils.get_all_java_files_data(self.debug)
        match args[0]:
            case "basic":
                self.ui_file = "basic_field.lua"
                self.data = [
                    {
                        "name": f"{v[0]} ({v[1]})",
                        "id": f"{v[1]}.{v[0]}",
                        "type": f"{v[0]}",
                        "package_path": f"{v[1]}",
                    }
                    for v in self.java_basic_types
                ]
            case "id":
                self.ui_file = "id_field.lua"
                self.data = [
                    {
                        "name": f"{v[0]} ({v[1]})",
                        "id": f"{v[1]}.{v[0]}",
                        "type": f"{v[0]}",
                        "package_path": f"{v[1]}",
                    }
                    for v in self.java_basic_types
                    if v[0] in ["Long", "Integer", "String", "UUID"]
                ]
            case "enum":
                self.ui_file = "enum_field.lua"
                all_enum_files = [
                    f
                    for f in self.all_java_files
                    if f.declaration_type == DeclarationType.ENUM
                ]
                self.data = [
                    {
                        "name": f"{v.file_name} ({v.package_path})",
                        "package_path": f"{v.package_path}",
                        "type": f"{v.file_name}",
                        "id": f"{v.path}",
                    }
                    for v in all_enum_files
                ]
            case _:
                error_msg = "Unable to get ui file"
                self.logging.log(error_msg, LogLevel.ERROR)
                raise FileNotFoundError(error_msg)

    def get_buffer_file_data(
        self, current_buffer_tree: Tree, buffer_path: Path, debug: bool = False
    ) -> JavaFileData:
        for file in self.all_java_files:
            if file.path == buffer_path:
                file.tree = current_buffer_tree
                return file
        error_msg = "Unable to get owning side buffer data"
        if debug:
            self.logging.log(error_msg, LogLevel.ERROR)
        raise FileNotFoundError(error_msg)

    @command("CreateEntityField", nargs="*")
    def create_entity_field(self, args) -> None:
        self.process_command_args(args)
        buffer_tree = self.treesitter_utils.convert_buffer_to_tree(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        self.buffer_file_data = self.get_buffer_file_data(
            buffer_tree, buffer_path, self.debug
        )
        if self.buffer_file_data is None:
            error_msg = "Unable to get current buffer's file data"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise FileNotFoundError(error_msg)
        if self.buffer_file_data:
            snaked_class_name = self.common_utils.convert_to_snake_case(
                self.buffer_file_data.file_name, self.debug
            )
            self.nvim.exec_lua(
                self.common_utils.read_ui_file_as_string(self.ui_file),
                (
                    str(self.path_utils.get_plugin_base_path().joinpath("ui")),
                    self.data,
                    snaked_class_name,
                ),
            )

    @function("CreateBasicEntityFieldCallback")
    def crease_basic_entity_field_callback(self, args: List[Dict]):
        converted_args = CreateBasicEntityFieldArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        if self.buffer_file_data:
            self.entity_field_utils.create_basic_entity_field(
                buffer_file_data=self.buffer_file_data,
                args=converted_args,
                debug=self.debug,
            )

    @function("CreateEnumEntityFieldCallback")
    def crease_enum_entity_field_callback(self, args):
        converted_args = CreateEnumEntityFieldArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        if self.buffer_file_data:
            self.entity_field_utils.create_enum_entity_field(
                buffer_file_data=self.buffer_file_data,
                args=converted_args,
                debug=self.debug,
            )

    @function("CreateIdEntityFieldCallback")
    def crease_id_entity_field_callback(self, args: List[Dict]):
        converted_args = CreateIdEntityFieldArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        if self.buffer_file_data:
            self.entity_field_utils.create_id_entity_field(
                buffer_file_data=self.buffer_file_data,
                args=converted_args,
                debug=self.debug,
            )
