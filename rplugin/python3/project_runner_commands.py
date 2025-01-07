from pynvim.api import Nvim
from pynvim import List, command, plugin

from base import Base
from custom_types.log_level import LogLevel


@plugin
class JpaRepoCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.debug: bool = False

    @command("BuildAndRunProject", nargs="*")
    def build_and_run_project(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        self.logging.log(args, LogLevel.DEBUG)
        if len(args) > 1:
            error_msg = "Only one argument allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        self.build_helper.run(self.debug)

    @command("BuildProject", nargs="*")
    def build__project(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        self.logging.log(args, LogLevel.DEBUG)
        if len(args) > 1:
            error_msg = "Only one argument allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        self.build_helper.build(self.debug)
