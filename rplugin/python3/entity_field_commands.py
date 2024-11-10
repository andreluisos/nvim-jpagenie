from pathlib import Path
from typing import Dict, List, Literal, Optional

from pynvim import plugin, command, function

from pynvim.api import Nvim
from tree_sitter import Tree

from base import Base
from custom_types.enum_type import EnumType
from custom_types.field_temporal import FieldTemporal
from custom_types.field_time_zone_storage import FieldTimeZoneStorage
from custom_types.declaration_type import DeclarationType
from custom_types.id_generation import IdGeneration
from custom_types.id_generation_type import IdGenerationType
from custom_types.log_level import LogLevel
from custom_types.java_file_data import JavaFileData


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
        if len(args) < 1 or len(args) > 2:
            error_msg = "At least one and max 2 arguments allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if len(args) == 2 else False
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
                self.file_utils.read_ui_file_as_string(self.ui_file),
                (self.ui_path, self.data, snaked_class_name),
            )

    @function("CreateBasicEntityFieldCallback")
    def crease_basic_entity_field_callback(self, args):
        if self.buffer_file_data:
            self.entity_field_utils.create_basic_entity_field(
                buffer_file_data=self.buffer_file_data,
                field_package_path=args[0]["field_package_path"],
                field_type=args[0]["field_type"],
                field_name=args[0]["field_name"],
                field_length=args[0]["field_length"],
                field_precision=args[0]["field_precision"],
                field_scale=args[0]["field_scale"],
                field_time_zone_storage=(
                    FieldTimeZoneStorage.from_value(args[0]["field_time_zone_storage"])
                    if "field_time_zone_storage" in args[0]
                    else None
                ),
                field_temporal=(
                    FieldTemporal(args[0]["field_temporal"])
                    if "field_temporal" in args[0]
                    else None
                ),
                mandatory=True if "mandatory" in args[0]["other"] else False,
                unique=True if "unique" in args[0]["other"] else False,
                large_object=True if "large_object" in args[0]["other"] else False,
                debug=self.debug,
            )

    @function("CreateEnumEntityFieldCallback")
    def crease_enum_entity_field_callback(self, args):
        if self.buffer_file_data:
            self.entity_field_utils.create_enum_entity_field(
                buffer_file_data=self.buffer_file_data,
                field_package_path=args[0]["field_package_path"],
                field_name=args[0]["field_name"],
                field_type=args[0]["field_type"],
                field_length=args[0]["field_length"],
                enum_type=EnumType.from_value(args[0]["enum_type"]),
                mandatory=True if "mandatory" in args[0]["other"] else False,
                unique=True if "unique" in args[0]["other"] else False,
                debug=self.debug,
            )

    @function("CreateIdEntityFieldCallback")
    def crease_id_entity_field_callback(self, args):
        if self.buffer_file_data:
            self.entity_field_utils.create_id_entity_field(
                buffer_file_data=self.buffer_file_data,
                field_package_path=args[0]["field_package_path"],
                field_type=args[0]["field_type"],
                field_name=args[0]["field_name"],
                id_generation=IdGeneration.from_value(args[0]["id_generation"]),
                id_generation_type=IdGenerationType.from_value(
                    args[0]["id_generation_type"]
                ),
                generator_name=(
                    args[0]["generator_name"]
                    if args[0]["id_generation_type"] == "entity_exclusive_generation"
                    else None
                ),
                sequence_name=(
                    args[0]["sequence_name"]
                    if args[0]["id_generation_type"] == "entity_exclusive_generation"
                    else None
                ),
                initial_value=(
                    int(args[0]["initial_value"])
                    if args[0]["id_generation_type"] == "entity_exclusive_generation"
                    and int(args[0]["initial_value"]) != 1
                    else None
                ),
                allocation_size=(
                    int(args[0]["allocation_size"])
                    if args[0]["id_generation_type"] == "entity_exclusive_generation"
                    and int(args[0]["allocation_size"]) != 50
                    else None
                ),
                mandatory=True if "mandatory" in args[0]["other"] else False,
            )
