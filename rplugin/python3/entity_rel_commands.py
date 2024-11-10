from pathlib import Path
from typing import Dict, List, Literal, Optional

from pynvim import plugin, command, function
from pynvim.api import Nvim
from tree_sitter import Tree

from base import Base
from custom_types.java_file_data import JavaFileData
from custom_types.log_level import LogLevel
from custom_types.create_many_to_one_args import CreateManyToOneRelArgs
from custom_types.create_one_to_one_args import CreateOneToOneRelArgs
from custom_types.create_many_to_many_args import CreateManyToManyRelArgs


@plugin
class EntityRelationshipCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.all_java_files: List[JavaFileData] = []
        self.owning_side_file_data: Optional[JavaFileData] = None
        self.inverse_side_file_data: Optional[JavaFileData] = None
        self.ui_file: Literal["many_to_one.lua", "many_to_many.lua", "one_to_one.lua"]
        self.debug: bool = False

    def process_command_args(self, args) -> None:
        self.logging.reset_log_file()
        self.logging.log(args, LogLevel.DEBUG)
        if len(args) < 1 or len(args) > 2:
            error_msg = "At least one and max 2 arguments allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        match args[0]:
            case "many-to-one":
                self.ui_file = "many_to_one.lua"
            case "many-to-many":
                self.ui_file = "many_to_many.lua"
            case "one-to-one":
                self.ui_file = "one_to_one.lua"
            case _:
                error_msg = "Unable to get ui file"
                self.logging.log(error_msg, LogLevel.ERROR)
                raise FileNotFoundError(error_msg)
        self.debug = args[1] if len(args) == 2 else False
        self.all_java_files = self.common_utils.get_all_java_files_data(self.debug)

    def get_owning_side_file_data(
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

    def get_inverse_side_file_data(
        self, field_type: str, debug: bool = False
    ) -> JavaFileData:
        for file in self.all_java_files:
            if file.file_name == field_type:
                for buf in self.nvim.buffers:
                    if buf.name and Path(buf.name).resolve() == file.path:
                        file.tree = self.treesitter_utils.convert_buffer_to_tree(buf)
                return file
        error_msg = "Unable to get inverse side buffer data"
        if debug:
            self.logging.log(error_msg, LogLevel.ERROR)
        raise FileNotFoundError(error_msg)

    @command("CreateEntityRelationship", nargs="*")
    def create_entity_relationship(self, args) -> None:
        self.process_command_args(args)
        buffer_tree = self.treesitter_utils.convert_buffer_to_tree(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        self.owning_side_file_data = self.get_owning_side_file_data(
            buffer_tree, buffer_path, self.debug
        )
        data = [
            {
                "name": f"{v.file_name} ({v.package_path})",
                "type": f"{v.file_name}",
                "id": f"{v.path}",
            }
            for v in self.all_java_files
            if v.path != buffer_path and v.is_jpa_entity
        ]
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string(self.ui_file),
            (self.ui_path, data),
        )

    @function("ManyToOneCallback")
    def many_to_one_callback(self, args: List[Dict]):
        converted_args = CreateManyToOneRelArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        self.inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        if self.owning_side_file_data and self.inverse_side_file_data:
            self.entity_relationship_utils.create_many_to_one_relationship_field(
                owning_side_file_data=self.owning_side_file_data,
                inverse_side_file_data=self.inverse_side_file_data,
                args=converted_args,
                debug=self.debug,
            )

    @function("OneToOneCallback")
    def one_to_one_callback(self, args):
        converted_args = CreateOneToOneRelArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        self.inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        if self.owning_side_file_data and self.inverse_side_file_data:
            self.entity_relationship_utils.create_one_to_one_relationship_field(
                owning_side_file_data=self.owning_side_file_data,
                inverse_side_file_data=self.inverse_side_file_data,
                args=converted_args,
                debug=self.debug,
            )

    @function("ManyToManyCallback")
    def many_to_many_callback(self, args: List[Dict]):
        converted_args = CreateManyToManyRelArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        self.inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        if self.owning_side_file_data and self.inverse_side_file_data:
            self.entity_relationship_utils.create_many_to_many_relationship_field(
                owning_side_file_data=self.owning_side_file_data,
                inverse_side_file_data=self.inverse_side_file_data,
                args=converted_args,
                debug=self.debug,
            )
