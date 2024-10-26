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
            {"name": f"{v[0]} ({v[1]})", "id": f"{v[1]}.{v[0]}", "type": f"{v[0]}"}
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
            field_type=args[0]["field_type"],
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

    @command("CreateEnumEntityField")
    def create_enum_entity_field(self) -> None:
        data = [
            {
                "name": f"{v[0]} ({v[1]})",
                "package_path": f"{v[1]}",
                "type": f"{v[0]}",
                "id": f"{v[2]}",
            }
            for v in self.path_lib.get_all_files_by_declaration_type("enum", True)
        ]
        self.nvim.exec_lua(
            self.file_reader.read_ui_file_as_string("enum_field.lua"),
            (self.ui_path, data),
        )

    @function("CreateEnumEntityFieldCallback")
    def crease_enum_entity_field_callback(self, args):
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_field_lib.create_enum_entity_field(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            field_package_path=args[0]["field_package_path"],
            field_name=args[0]["field_name"],
            field_type=args[0]["field_type"],
            field_length=args[0]["field_length"],
            enum_type=args[0]["enum_type"],
            mandatory=True if "mandatory" in args[0]["other"] else False,
            unique=True if "unique" in args[0]["other"] else False,
            debug=True,
        )

    @command("CreateIdEntityField")
    def create_id_entity_field(self) -> None:
        data = [
            {"name": f"{v[0]} ({v[1]})", "id": f"{v[1]}.{v[0]}", "type": f"{v[0]}"}
            for v in self.java_basic_types
            if v[0] in ["Long", "Integer", "String", "UUID"]
        ]
        buffer_path = Path(self.nvim.current.buffer.name)
        class_name = self.treesitter_lib.get_buffer_class_name(buffer_path, True)
        if class_name:
            snaked_class_name = self.common_helper.generate_snaked_field_name(
                class_name, True
            )
            self.nvim.exec_lua(
                self.file_reader.read_ui_file_as_string("id_field.lua"),
                (self.ui_path, data, snaked_class_name),
            )

    @function("CreateIdEntityFieldCallback")
    def crease_id_entity_field_callback(self, args):
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(
            self.nvim.current.buffer
        )
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_field_lib.create_id_entity_field(
            buffer_bytes=buffer_bytes,
            buffer_path=buffer_path,
            field_package_path=args[0]["field_package_path"],
            field_type=args[0]["field_type"],
            field_name=args[0]["field_name"],
            id_generation=args[0]["id_generation"],
            id_generation_type=(
                args[0]["id_generation_type"]
                if args[0]["id_generation"] == "sequence"
                else None
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
