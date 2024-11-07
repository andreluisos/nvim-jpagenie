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
        buffer_path = Path(self.nvim.current.buffer.name)
        self.jpa_repo_utils.create_jpa_repository(buffer_path=buffer_path, debug=True)
