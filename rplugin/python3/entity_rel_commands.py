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
            for k, v in self.path_utils.get_all_jpa_entities().items()
            if v[1] != buffer_path
        ]
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string("many_to_one.lua"),
            (self.ui_path, data),
        )

    @function("ManyToOneCallback")
    def many_to_one_callback(self, args):
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_utils.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_rel_utils.create_many_to_one_relationship_field(
            owning_side_buffer_bytes=buffer_bytes,
            owning_side_buffer_path=buffer_path,
            collection_type=args[0]["collection_type"],
            fetch_type=args[0]["fetch_type"],
            mapping_type=args[0]["mapping_type"],
            inverse_side_type=args[0]["inverse_field_type"],
            owning_side_cascades=args[0]["owning_side_cascades"],
            inverse_side_cascades=args[0]["inverse_side_cascades"],
            inverse_side_other=args[0]["inverse_side_other"],
            owning_side_other=args[0]["owning_side_other"],
            debug=True,
        )

    @command("CreateOneToOneRelationship")
    def create_one_to_one_relationship(self) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        data = [
            {"name": f"{k} ({v[0]})", "id": k}
            for k, v in self.path_utils.get_all_jpa_entities().items()
            if v[1] != buffer_path
        ]
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string("one_to_one.lua"),
            (self.ui_path, data),
        )

    @function("OneToOneCallback")
    def one_to_one_callback(self, args):
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_rel_utils.create_one_to_one_relationship_field(
            owning_side_buffer_path=buffer_path,
            inverse_side_type=args[0]["inverse_field_type"],
            mapping_type=args[0]["mapping_type"],
            owning_side_cascades=args[0]["owning_side_cascades"],
            inverse_side_cascades=args[0]["inverse_side_cascades"],
            inverse_side_other=args[0]["inverse_side_other"],
            owning_side_other=args[0]["owning_side_other"],
            debug=True,
        )

    @command("CreateManyToManyRelationship")
    def create_many_to_many_relationship(self) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        data = [
            {"name": f"{k} ({v[0]})", "id": k}
            for k, v in self.path_utils.get_all_jpa_entities().items()
            if v[1] != buffer_path
        ]
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string("many_to_many.lua"),
            (self.ui_path, data),
        )

    @function("ManyToManyCallback")
    def many_to_many_callback(self, args):
        buffer_path = Path(self.nvim.current.buffer.name)
        self.entity_rel_utils.create_many_to_many_relationship_field(
            owning_side_buffer_path=buffer_path,
            inverse_side_type=args[0]["inverse_field_type"],
            mapping_type=args[0]["mapping_type"],
            owning_side_cascades=args[0]["owning_side_cascades"],
            inverse_side_cascades=args[0]["inverse_side_cascades"],
            inverse_side_other=args[0]["inverse_side_other"],
            debug=True,
        )
