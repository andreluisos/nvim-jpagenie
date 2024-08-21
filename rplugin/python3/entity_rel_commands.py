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
    def generate_id_entity_field(self, args: List[str]) -> None:
        # arg0 field_type (str)
        # arg1 cascade_persist (bool)
        # arg2 cascade_merge (bool)
        # arg3 cascade_remove (bool)
        # arg4 cascade_refresh (bool)
        # arg5 cascade_detach (bool)
        # arg6 fetch_type (none | lazy | eager)
        # arg7 mapping_type (unidirectional_joincolumn | bidirectional_joincolumn)
        # arg8 nullable (bool)
        # arg9 unique (bool)
        attach_debugger: bool = self.arg_validator.attach_debugger(args)
        if attach_debugger:
            self.logging.log(f"args:\n{args}", "debug")
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 11)
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
                "mapping_type",
                "bool",
                "bool",
            ],
        )
        self.entity_rel_lib.create_many_to_one_relationship(
            buffer_bytes, buffer_path, *validated_args, debug=attach_debugger
        )
