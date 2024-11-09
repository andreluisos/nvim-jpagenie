from typing import Optional
from pynvim import plugin, command, function
from pynvim.api import Nvim

from base import Base
from custom_types.entity_type import EntityType


@plugin
class EntityCreationCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateNewJpaEntity")
    def create_new_jpa_entity(self) -> None:
        self.logging.reset_log_file()
        found_entities = [
            e
            for e in self.common_utils.get_all_java_files_data(True)
            if e.is_jpa_entity
        ]
        parent_entities = [
            {
                "name": f"{v.file_name} ({v.package_path})",
                "id": f"{str(v.path)}",
                "type": f"{v.file_name}",
                "package_path": f"{v.package_path}",
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

    @function("CreateNewJpaEntityCallback")
    def many_to_one_callback(self, args):
        package_path: str = str(args[0]["package_path"])
        entity_name: str = str(args[0]["entity_name"])
        entity_type: EntityType = args[0]["entity_type"]
        parent_entity_type: Optional[str] = (
            args[0]["parent_entity_type"] if "parent_entity_type" in args[0] else None
        )
        parent_entity_package_path: Optional[str] = (
            args[0]["parent_entity_package_path"]
            if "parent_entity_package_path" in args[0]
            else None
        )
        self.entity_creation_utils.create_new_entity(
            package_path=package_path,
            entity_name=entity_name,
            entity_type=entity_type,
            parent_entity_type=parent_entity_type,
            parent_entity_package_path=parent_entity_package_path,
            debug=True,
        )
