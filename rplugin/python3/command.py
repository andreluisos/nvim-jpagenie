from pathlib import Path
from typing import Literal

from pynvim.api.nvim import Nvim
from pynvim.plugin import command, plugin

from createjavafile import CreateJavaFile
from messaging import Messaging
from pathutil import PathUtil
from tsutil import TreesitterUtil
from createjparepo import CreateJpaRepository


@plugin
class Command(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.messaging = Messaging(nvim)
        self.tsutil = TreesitterUtil(self.cwd, self.messaging)
        self.pathutil = PathUtil(self.cwd, self.tsutil, self.messaging)
        self.java_file = CreateJavaFile(self.nvim, self.messaging)
        self.jpa_repo = CreateJpaRepository(
            self.nvim, self.tsutil, self.pathutil, self.messaging
        )

    @command("CreateJavaFile", nargs="*")
    def create_java_file(self, args) -> None:
        self.messaging.log(
            f"Called CreateJavaFile command with the following args: {args}.", "debug"
        )
        if len(args) != 3:
            self.messaging.log(
                "Invalid number of arguments. Expected 3.", "error", send_msg=True
            )
            return
        package_path: str = args[0]
        file_name: str = args[1]
        file_type: Literal["class", "interface", "record", "enum", "annotation"] = args[
            2
        ]
        main_class_path = self.pathutil.get_spring_main_class_path()
        if main_class_path is None:
            self.messaging.log(
                "Spring main class path not found", "error", send_msg=True
            )
            return
        self.java_file.create_java_file(
            main_class_path=main_class_path,
            package_path=package_path,
            file_name=file_name,
            file_type=file_type,
            debugger=True,
        )

    @command("CreateJPARepository")
    def create_jpa_repository(self) -> None:
        root_path = self.pathutil.spring_project_root_path
        if root_path is None:
            self.messaging.log(
                "Unable to find the Spring root path. Is this a Spring Boot project?",
                "error",
                send_msg=True,
            )
            return
        self.jpa_repo.create_jpa_entity_for_buffer(Path(root_path), debugger=True)
