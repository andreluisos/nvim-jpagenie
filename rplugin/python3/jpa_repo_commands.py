from pathlib import Path

from pynvim.api import Nvim
from pynvim import List, command, plugin

from base import Base
from custom_types.log_level import LogLevel


@plugin
class JpaRepoCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateJPARepository", nargs="*")
    def create_jpa_repo_repository(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        self.logging.log(args, LogLevel.DEBUG)
        if len(args) > 1:
            error_msg = "At least one and max 2 arguments allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        buffer_path = Path(self.nvim.current.buffer.name)
        self.logging.echomsg(f"{self.debug}")
        self.jpa_repo_utils.create_jpa_repository(
            buffer_path=buffer_path, debug=self.debug
        )
