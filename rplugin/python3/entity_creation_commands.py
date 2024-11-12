from typing import Dict, List
from pynvim import plugin, command, function
from pynvim.api import Nvim

from base import Base
from custom_types.create_entity_args import CreateEntityArgs
from custom_types.log_level import LogLevel


@plugin
class EntityCreationCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.debug: bool = False

    @command("CreateNewJPAEntity", nargs="*")
    def create_new_jpa_entity(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        if len(args) > 1:
            error_msg = "Only one arg is allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        found_entities = [
            e
            for e in self.common_utils.get_all_java_files_data(True)
            if e.is_jpa_entity or e.is_mapped_superclass
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
    def many_to_one_callback(self, args: List[Dict]):
        converted_args = CreateEntityArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        self.entity_creation_utils.create_new_entity(
            args=converted_args,
            debug=self.debug,
        )
