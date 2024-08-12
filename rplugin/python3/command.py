from pathlib import Path
from typing import Literal

from pynvim.api.nvim import Nvim
from pynvim.plugin import command, plugin

from createjavafile import CreateJavaFile
from messaging import Messaging
from pathutil import PathUtil
from createentityfield import CreateEntityField
from tsutil import TreesitterUtil
from createjparepo import CreateJpaRepository
from constants.java_types import JAVA_TYPES


@plugin
class Command(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.java_types = JAVA_TYPES
        self.messaging = Messaging(nvim)
        self.tsutil = TreesitterUtil(self.nvim, self.cwd, self.messaging)
        self.pathutil = PathUtil(self.cwd, self.tsutil, self.messaging)
        self.java_file = CreateJavaFile(self.nvim, self.messaging)
        self.jpa_repo = CreateJpaRepository(
            self.nvim, self.tsutil, self.pathutil, self.messaging
        )
        self.entity_field = CreateEntityField(self.nvim, self.tsutil, self.messaging)

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
        self.jpa_repo.create_jpa_entity_for_current_buffer(
            Path(root_path), debugger=True
        )

    @command("GenerateBasicEntityField", nargs="*")
    def generate_basic_entity_field(self, args) -> None:
        current_buffer = Path(self.nvim.current.buffer.name)
        if len(args) < 5:
            error_msg = "At least 5 arguments are necessary."
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)
        if args[0] not in [k[0] for k in self.java_types]:
            error_msg = "Invalid field type."
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)
        field_name = args[1]
        if not isinstance(field_name, str):
            error_msg = "Field name must be a string."
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)
        try:
            nullable = args[2].lower() in ("true", "1", "yes")
            unique = args[3].lower() in ("true", "1", "yes")
            large_object = args[4].lower() in ("true", "1", "yes")
        except ValueError:
            error_msg = "Nullable, unique, and large object must be boolean."
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)
        if not self.tsutil.is_buffer_jpa_entity(current_buffer):
            error_msg = "Current buffer isn't a JPA Entity"
            self.messaging.log(error_msg, "error")
            raise ValueError(error_msg)
        self.entity_field.create_basic_entity_field(
            current_buffer,
            args[0],
            field_name,
            nullable,
            unique,
            large_object,
            True,
        )
