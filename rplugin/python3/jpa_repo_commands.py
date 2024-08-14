from pathlib import Path

from pynvim.plugin import command

from base import Base


class JpaRepoCommands(Base):
    def __init__(self) -> None:
        super()

    @command("CreateJPARepository")
    def create_jpa_repo_libsitory(self) -> None:
        root_path = self.path_lib.spring_project_root_path
        if root_path is None:
            error_msg = (
                "Unable to find the Spring root path. Is this a Spring Boot project?"
            )
            self.logging.log(
                error_msg,
                "error",
            )
            raise ValueError(error_msg)
        self.jpa_repo_lib.create_jpa_entity_for_current_buffer(
            Path(root_path), debugger=True
        )
