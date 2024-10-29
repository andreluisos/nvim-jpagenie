from pathlib import Path

from pynvim.api import Nvim
from pynvim import command, plugin

from base import Base


@plugin
class JpaRepoCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateJPARepository")
    def create_jpa_repo_repository(self) -> None:
        self.logging.reset_log_file()
        root_path = self.path_utils.spring_project_root_path
        self.jpa_repo_utils.create_jpa_entity_for_current_buffer(
            Path(root_path), debug=True
        )
