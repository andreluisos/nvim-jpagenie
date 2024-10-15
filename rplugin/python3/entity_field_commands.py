from pathlib import Path

from pynvim import plugin, command, function

from pynvim.api import Nvim

from base import Base


@plugin
class EntityFieldCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateBasicEntityField")
    def create_basic_entity_field(self) -> None:
        data = [
            {"name": f"{v[0]} ({v[1]})", "id": f"{v[1]}.{v[0]}"}
            for v in self.java_basic_types
        ]
        self.nvim.exec_lua(
            self.file_reader.read_ui_file_as_string("basic_field.lua"),
            (self.ui_path, data),
        )

    @function("CreateBasicEntityFieldCallback")
    def crease_basic_entity_field_callback(self, args):
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_field_lib.create_basic_entity_field(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            field_package_path=args[0]["field_package_path"],
            field_name=args[0]["field_name"],
            field_length=args[0]["field_length"],
            field_precision=args[0]["field_precision"],
            field_scale=args[0]["field_scale"],
            field_time_zone_storage=(
                args[0]["field_time_zone_storage"]
                if "field_time_zone_storage" in args[0]
                else None
            ),
            field_temporal=(
                args[0]["field_temporal"] if "field_temporal" in args[0] else None
            ),
            mandatory=True if "mandatory" in args[0]["other"] else False,
            unique=True if "unique" in args[0]["other"] else False,
            large_object=True if "large_object" in args[0]["other"] else False,
            debug=True,
        )

    # @command("GenerateIdField", nargs="*")
    # def generate_id_entity_field(self, args: List[str]) -> None:
    #     # arg0 field_type (Long | Integer | String | UUID - java_type)
    #     # arg1 field_name (str)
    #     # arg2 id_generation (none | auto | identity | sequence)
    #     # arg3 nullable (bool)
    #     attach_debugger: bool = self.arg_validator.attach_debugger(args)
    #     if attach_debugger:
    #         self.logging.log(f"args:\n{args}", "debug")
    #     current_buffer: Buffer = self.nvim.current.buffer
    #     buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.arg_validator.validate_args_length(args, 4)
    #     validated_args = self.arg_validator.validate_args_type(
    #         args, ["id_type", "str", "id_gen_type", "bool"]
    #     )
    #     self.entity_field_lib.create_id_entity_field(
    #         buffer_bytes, buffer_path, *validated_args, debug=attach_debugger
    #     )
    #
    # @command("GenerateBasicEntityField", nargs="*")
    # def generate_basic_entity_field_lib(self, args: List[str]) -> None:
    #     # arg0 = field_type (java_type)
    #     # arg1 = field_name (str)
    #     # arg2 = nullable (bool)
    #     # arg3 = unique (bool)
    #     # arg4 = large_object (bool)
    #     attach_debugger: bool = self.arg_validator.attach_debugger(args)
    #     if attach_debugger:
    #         self.logging.log(f"args:\n{args}", "debug")
    #     current_buffer: Buffer = self.nvim.current.buffer
    #     buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.arg_validator.validate_args_length(args, 5)
    #     validated_args = self.arg_validator.validate_args_type(
    #         args, ["java_type", "str", "bool", "bool", "bool"]
    #     )
    #     self.entity_field_lib.create_basic_entity_field(
    #         buffer_bytes,
    #         buffer_path,
    #         *validated_args,
    #         debug=attach_debugger,
    #     )
    #
    # @command("GeneratedEnumEntityField", nargs="*")
    # def generate_enum_entity_field(self, args: List[str]) -> None:
    #     # arg0 = field_type (str)
    #     # arg1 = field_name (str)
    #     # arg2 = enum_type (ORDINAL | STRING)
    #     # arg3 = string_length (int)
    #     # arg4 = nullable (bool)
    #     # arg5 = unique (bool)
    #     attach_debugger: bool = self.arg_validator.attach_debugger(args)
    #     if attach_debugger:
    #         self.logging.log(f"args:\n{args}", "debug")
    #     current_buffer: Buffer = self.nvim.current.buffer
    #     buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.arg_validator.validate_args_length(args, 6)
    #     validated_args = self.arg_validator.validate_args_type(
    #         args, ["str", "str", "enum", "int", "bool", "bool"]
    #     )
    #     self.entity_field_lib.create_enum_entity_field(
    #         buffer_bytes,
    #         buffer_path,
    #         *validated_args,
    #         debug=attach_debugger,
    #     )
