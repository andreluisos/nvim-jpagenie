from pynvim import plugin, command, function
from pynvim.api import Nvim

from base import Base


@plugin
class EntityCreationCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateNewJpaEntity")
    def create_new_jpa_entity(self) -> None:
        found_entities = self.entity_creation_utils.fetch_entity_data(debug=True)
        parent_entities = [
            {
                "name": f"{v[0]} ({v[1]})",
                "id": f"{v[2]}",
                "type": f"{v[0]}",
                "package_path": f"{v[1]}",
            }
            for v in found_entities
        ]
        root_package_path = str(self.path_utils.get_spring_root_package_path(True))
        self.nvim.exec_lua(
            self.file_utils.read_ui_file_as_string("create_entity.lua"),
            (
                self.ui_path,
                parent_entities,
                root_package_path,
            ),
        )
        pass

    @function("CreateNewJpaEntityCallback")
    def many_to_one_callback(self, args):
        self.entity_creation_utils.create_new_entity(
            package_path=args[0]["package_path"],
            entity_name=args[0]["entity_name"],
            entity_type=args[0]["entity_type"],
            parent_entity_type=(
                args[0]["parent_entity_type"]
                if "parent_entity_type" in args[0]
                else None
            ),
            parent_entity_package_path=(
                args[0]["parent_entity_package_path"]
                if "parent_entity_package_path" in args[0]
                else None
            ),
            debug=True,
        )
