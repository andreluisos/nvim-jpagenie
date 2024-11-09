from pathlib import Path
from typing import List, Literal, Optional

from pynvim import plugin, command, function
from pynvim.api import Nvim
from tree_sitter import Tree

from base import Base
from custom_types.other import Other
from custom_types.cascade_type import CascadeType
from custom_types.collection_type import CollectionType
from custom_types.fetch_type import FetchType
from custom_types.mapping_type import MappingType
from custom_types.java_file_data import JavaFileData
from custom_types.log_level import LogLevel


@plugin
class EntityRelationshipCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.all_java_files: List[JavaFileData] = []
        self.owning_side_buffer_tree: Optional[JavaFileData] = None
        self.inverse_side_buffer_tree: Optional[JavaFileData] = None
        self.ui_file: Literal["many_to_one.lua", "many_to_many.lua", "one_to_one.lua"]
        self.debug: bool = False

    def process_command_args(self, args) -> None:
        self.logging.reset_log_file()
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
        current_buffer_path = Path(self.nvim.current.buffer.name)
        data = [
            {
                "name": f"{v.file_name} ({v.package_path})",
                "type": f"{v.file_name}",
                "id": f"{v.path}",
            }
            for v in self.all_java_files
            if v.path != current_buffer_path and v.is_jpa_entity
        ]
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string(self.ui_file),
            (self.ui_path, data),
        )

    @function("ManyToOneCallback")
    def many_to_one_callback(self, args):
        buffer_tree = self.treesitter_utils.convert_buffer_to_tree(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        owning_side_file_data = self.get_owning_side_file_data(
            buffer_tree, buffer_path, self.debug
        )
        inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        self.entity_relationship_utils.create_many_to_one_relationship_field(
            owning_side_file_data=owning_side_file_data,
            inverse_side_file_data=inverse_side_file_data,
            collection_type=CollectionType.from_value(args[0]["collection_type"]),
            fetch_type=FetchType.from_value(args[0]["fetch_type"]),
            mapping_type=MappingType.from_value(args[0]["mapping_type"]),
            owning_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["owning_side_cascades"]
            ],
            inverse_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["inverse_side_cascades"]
            ],
            inverse_side_other=[
                Other.from_value(c) for c in args[0]["inverse_side_other"]
            ],
            owning_side_other=[
                Other.from_value(c) for c in args[0]["owning_side_other"]
            ],
            debug=self.debug,
        )

    @function("OneToOneCallback")
    def one_to_one_callback(self, args):
        buffer_tree = self.treesitter_utils.convert_buffer_to_tree(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        owning_side_file_data = self.get_owning_side_file_data(
            buffer_tree, buffer_path, self.debug
        )
        inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        self.entity_relationship_utils.create_one_to_one_relationship_field(
            owning_side_file_data=owning_side_file_data,
            inverse_side_file_data=inverse_side_file_data,
            mapping_type=MappingType.from_value(args[0]["mapping_type"]),
            owning_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["owning_side_cascades"]
            ],
            inverse_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["inverse_side_cascades"]
            ],
            inverse_side_other=[
                Other.from_value(c) for c in args[0]["inverse_side_other"]
            ],
            owning_side_other=[
                Other.from_value(c) for c in args[0]["owning_side_other"]
            ],
            debug=self.debug,
        )

    @function("ManyToManyCallback")
    def many_to_many_callback(self, args):
        buffer_tree = self.treesitter_utils.convert_buffer_to_tree(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        owning_side_file_data = self.get_owning_side_file_data(
            buffer_tree, buffer_path, self.debug
        )
        inverse_side_file_data = self.get_inverse_side_file_data(
            args[0]["inverse_field_type"]
        )
        self.entity_relationship_utils.create_many_to_many_relationship_field(
            owning_side_file_data=owning_side_file_data,
            inverse_side_file_data=inverse_side_file_data,
            mapping_type=MappingType.from_value(args[0]["mapping_type"]),
            owning_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["owning_side_cascades"]
            ],
            inverse_side_cascades=[
                CascadeType.from_value(c) for c in args[0]["inverse_side_cascades"]
            ],
            inverse_side_other=[
                Other.from_value(c) for c in args[0]["inverse_side_other"]
            ],
            debug=self.debug,
        )
