from pathlib import Path
from typing import List

from pynvim import plugin
from pynvim.api import Buffer, Nvim
from pynvim.plugin import command

from base import Base


@plugin
class EntityRelationshipCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateManyToOneRelationship", nargs="*")
    def create_many_to_one_relationship(self, args: List[str]) -> None:
        # arg0 inverse_field_type (str)
        # arg1 cascade_persist (bool)
        # arg2 cascade_merge (bool)
        # arg3 cascade_remove (bool)
        # arg4 cascade_refresh (bool)
        # arg5 cascade_detach (bool)
        # arg6 fetch_type (none | lazy | eager)
        # arg7 mandatory (bool)
        # arg8 unique (bool)
        attach_debugger: bool = self.arg_validator.attach_debugger(args)
        if attach_debugger:
            self.logging.log(f"args:\n{args}", "debug")
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 9)
        validated_args = self.arg_validator.validate_args_type(
            args,
            [
                "str",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "fetch_type",
                "bool",
                "bool",
            ],
        )
        self.entity_rel_lib.create_many_to_one_relationship_field(
            buffer_bytes, buffer_path, *validated_args, debug=attach_debugger
        )

    @command("CreateOneToManyRelationship", nargs="*")
    def create_one_to_many_relationship(self, args: List[str]) -> None:
        # arg0 inverse_field_type (str)
        # arg1 collection_type (set | list | collection)
        # arg2 orphan_removal (bool)
        # arg3 cascade_persist (bool)
        # arg4 cascade_merge (bool)
        # arg5 cascade_remove (bool)
        # arg6 cascade_refresh (bool)
        # arg7 cascade_detach (bool)
        attach_debugger: bool = self.arg_validator.attach_debugger(args)
        if attach_debugger:
            self.logging.log(f"args:\n{args}", "debug")
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 8)
        validated_args = self.arg_validator.validate_args_type(
            args,
            [
                "str",
                "collection_type",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
            ],
        )
        self.entity_rel_lib.create_one_to_many_relationship_field(
            buffer_path, *validated_args, debug=attach_debugger
        )

    @command("CreateOneToOneOwningRelationship", nargs="*")
    def create_one_to_one_owning_side_relationship(self, args: List[str]) -> None:
        # arg0 inverse_field_type (str)
        # arg1 cascade_persist (bool)
        # arg2 cascade_merge (bool)
        # arg3 cascade_remove (bool)
        # arg4 cascade_refresh (bool)
        # arg5 cascade_detach (bool)
        # arg6 mandatory (bool)
        # arg7 unique (bool)
        # arg8 orphan_removal (bool)
        attach_debugger: bool = self.arg_validator.attach_debugger(args)
        if attach_debugger:
            self.logging.log(f"args:\n{args}", "debug")
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 9)
        validated_args = self.arg_validator.validate_args_type(
            args,
            [
                "str",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
            ],
        )
        self.entity_rel_lib.create_one_to_one_owning_side_relationship_field(
            buffer_bytes, buffer_path, *validated_args, debug=attach_debugger
        )

    @command("CreateOneToOneInverseRelationship", nargs="*")
    def create_one_to_one_inverse_side_relationship(self, args: List[str]) -> None:
        # arg0 inverse_field_type (str)
        # arg1 cascade_persist (bool)
        # arg2 cascade_merge (bool)
        # arg3 cascade_remove (bool)
        # arg4 cascade_refresh (bool)
        # arg5 cascade_detach (bool)
        # arg6 mandatory (bool)
        # arg7 unique (bool)
        # arg8 orphan_removal (bool)
        attach_debugger: bool = self.arg_validator.attach_debugger(args)
        if attach_debugger:
            self.logging.log(f"args:\n{args}", "debug")
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 9)
        validated_args = self.arg_validator.validate_args_type(
            args,
            [
                "str",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
                "bool",
            ],
        )
        self.entity_rel_lib.create_one_to_one_inverse_side_relationship_field(
            buffer_path, *validated_args, debug=attach_debugger
        )
