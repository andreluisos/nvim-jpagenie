from pathlib import Path

from pynvim.api import Buffer
from pynvim import plugin
from pynvim.api import Buffer, Nvim
from pynvim.plugin import command

from base import Base


@plugin
class EntityFieldCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("GenerateBasicEntityField", nargs="*")
    def generate_basic_entity_field_lib(self, args) -> None:
        # arg0 = field_type (java_type)
        # arg1 = field_name (str)
        # arg2 = nullable (bool)
        # arg3 = unique (bool)
        # arg4 = large_object (bool)
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 5)
        validated_args = self.arg_validator.validate_args_type(
            args, ["java_type", "str", "bool", "bool", "bool"]
        )
        self.entity_field_lib.create_basic_entity_field(
            buffer_bytes,
            buffer_path,
            *validated_args,
            debugger=True,
        )

    @command("GeneratedEnumEntityField", nargs="*")
    def generate_enum_entity_field(self, args) -> None:
        # arg0 = field_type (str)
        # arg1 = field_name (str)
        # arg2 = enum_type (ORDINAL | STRING)
        # arg3 = string_length (int)
        # arg4 = nullable (bool)
        # arg5 = unique (bool)
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 6)
        validated_args = self.arg_validator.validate_args_type(
            args, ["str", "str", "enum", "int", "bool", "bool"]
        )
        self.entity_field_lib.create_enum_entity_field(
            buffer_bytes,
            buffer_path,
            *validated_args,
            debugger=True,
        )
