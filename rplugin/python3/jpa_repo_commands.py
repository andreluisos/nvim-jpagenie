from pathlib import Path
from typing import List, Optional

from pynvim.api import Nvim
from pynvim import command, plugin

from base import Base


@plugin
class JpaRepoCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateJPARepository", nargs="*")
    def create_jpa_repo_repository(self, args: Optional[List[str]]) -> None:
        # Optional arg: debug
        attach_debugger: bool = False
        if args:
            attach_debugger: bool = self.arg_validator.attach_debugger(args)
            if attach_debugger:
                self.logging.log(f"args:\n{args}", "debug")
            else:
                self.arg_validator.validate_args_length(args, 0)
        root_path = self.path_lib.spring_project_root_path
        self.jpa_repo_lib.create_jpa_entity_for_current_buffer(
            Path(root_path), debug=True
        )
