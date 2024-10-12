from pathlib import Path

from pynvim import plugin, command, function
from pynvim.api import Buffer, Nvim

from base import Base


@plugin
class EntityRelationshipCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateManyToOneRelationship")
    def create_many_to_one_relationship(self) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        data = [
            {"name": f"{k} ({v[0]})", "id": k}
            for k, v in self.path_lib.get_all_jpa_entities().items()
            if v[1] != buffer_path
        ]
        self.nvim.exec_lua(
            self.file_reader.read_ui_file_as_string("many_to_one.lua"),
            (self.ui_path, data),
        )

    @function("ManyToOneCallback")
    def many_to_one_callback(self, args):
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_rel_lib.create_many_to_one_relationship_field(
            owning_side_buffer_bytes=buffer_bytes,
            owning_side_buffer_path=buffer_path,
            collection_type=args[0]["collection_type"],
            fetch_type=args[0]["fetch_type"],
            mapping_type=args[0]["mapping_type"],
            inverse_side_type=args[0]["inverse_field_type"],
            owning_side_cascades=args[0]["owning_side_cascades"],
            inverse_side_cascades=args[0]["inverse_side_cascades"],
            orphan_removal=args[0]["orphan_removal"],
            selected_other=args[0]["selected_other"],
            debug=True,
        )

    # @command("CreateOneToManyRelationship")
    # def create_one_to_many_relationship(self) -> None:
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     data = [
    #         {"name": f"{k} ({v[0]})", "id": k}
    #         for k, v in self.path_lib.get_all_jpa_entities().items()
    #         if v[1] != buffer_path
    #     ]
    #     self.nvim.exec_lua(
    #         self.file_reader.read_ui_file_as_string("one_to_many.lua"),
    #         (self.ui_path, data),
    #     )
    #
    # @function("OneToManyCallback")
    # def one_to_many_callback(self, args):
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.entity_rel_lib.create_one_to_many_relationship_field(
    #         owning_side_buffer_path=buffer_path,
    #         inverse_side_type=str(args[0]["inverse_field_type"]),
    #         cascade_persist=bool(args[0]["cascade_persist"]),
    #         cascade_merge=bool(args[0]["cascade_merge"]),
    #         cascade_remove=bool(args[0]["cascade_remove"]),
    #         cascade_refresh=bool(args[0]["cascade_refresh"]),
    #         cascade_detach=bool(args[0]["cascade_detach"]),
    #         collection_type=str(args[0]["collection_type"]),
    #         orphan_removal=bool(args[0]["orphan_removal"]),
    #     )
    #     return args[0]
    #
    # @command("CreateOneToOneRelationship", nargs="*")
    # def create_one_to_one_relationship(self, args: List[str]) -> None:
    #     # arg0 inverse_field_type (str)
    #     # arg1 cascade_persist (bool)
    #     # arg2 cascade_merge (bool)
    #     # arg3 cascade_remove (bool)
    #     # arg4 cascade_refresh (bool)
    #     # arg5 cascade_detach (bool)
    #     # arg6 mandatory (bool)
    #     # arg7 unique (bool)
    #     # arg8 orphan_removal (bool)
    #     # arg9 owning_side (bool)
    #     attach_debugger: bool = self.arg_validator.attach_debugger(args)
    #     if attach_debugger:
    #         self.logging.log(f"args:\n{args}", "debug")
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.arg_validator.validate_args_length(args, 10)
    #     validated_args = self.arg_validator.validate_args_type(
    #         args,
    #         [
    #             "str",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #         ],
    #     )
    #     self.entity_rel_lib.create_one_to_one_relationship_field(
    #         buffer_path, *validated_args, debug=attach_debugger
    #     )
    #
    # @command("CreateManyToManyRelationship", nargs="*")
    # def create_many_to_many_owning_side_relationship(self, args: List[str]) -> None:
    #     # arg0 inverse_field_type (str)
    #     # arg1 cascade_persist (bool)
    #     # arg2 cascade_merge (bool)
    #     # arg3 cascade_refresh (bool)
    #     # arg4 cascade_detach (bool)
    #     # arg5 collection_type (set | list | collection)
    #     # arg6 owning_side (bool)
    #     attach_debugger: bool = self.arg_validator.attach_debugger(args)
    #     if attach_debugger:
    #         self.logging.log(f"args:\n{args}", "debug")
    #     buffer_path = Path(self.nvim.current.buffer.name)
    #     self.arg_validator.validate_args_length(args, 7)
    #     validated_args = self.arg_validator.validate_args_type(
    #         args,
    #         [
    #             "str",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "bool",
    #             "collection_type",
    #             "bool",
    #         ],
    #     )
    #     self.entity_rel_lib.create_many_to_many_relationship_field(
    #         buffer_path, *validated_args, debug=attach_debugger
    #     )
