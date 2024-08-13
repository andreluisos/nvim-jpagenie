from pathlib import Path

from pynvim.api.nvim import Nvim
from pynvim.plugin import command, plugin

from createjavafile import CreateJavaFile
from messaging import Messaging
from pathutil import PathUtil
from createentityfield import CreateEntityField
from argvalidator import ArgValidator
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
        self.arg_validator = ArgValidator(self.messaging)
        self.tsutil = TreesitterUtil(self.nvim, self.cwd, self.messaging)
        self.pathutil = PathUtil(self.cwd, self.tsutil, self.messaging)
        self.java_file = CreateJavaFile(self.nvim, self.messaging)
        self.jpa_repo = CreateJpaRepository(
            self.nvim, self.tsutil, self.pathutil, self.messaging
        )
        self.entity_field = CreateEntityField(self.nvim, self.tsutil, self.messaging)

    @command("CreateJavaFile", nargs="*")
    def create_java_file(self, args) -> None:
        # arg0 = package_path (str)
        # arg1 = file_name (str)
        # arg2 = file_type (java_file)
        self.arg_validator.validate_args_length(args, 3)
        validated_args = self.arg_validator.validate_args_type(
            args, ["str", "str", "java_file"]
        )
        main_class_path = self.pathutil.get_spring_main_class_path()
        self.java_file.create_java_file(
            main_class_path,
            *validated_args,
            debugger=True,
        )

    @command("CreateJPARepository")
    def create_jpa_repository(self) -> None:
        root_path = self.pathutil.spring_project_root_path
        if root_path is None:
            error_msg = (
                "Unable to find the Spring root path. Is this a Spring Boot project?"
            )
            self.messaging.log(
                error_msg,
                "error",
            )
            raise ValueError(error_msg)
        self.jpa_repo.create_jpa_entity_for_current_buffer(
            Path(root_path), debugger=True
        )

    @command("GenerateBasicEntityField", nargs="*")
    def generate_basic_entity_field(self, args) -> None:
        # arg0 = field_type (java_type)
        # arg1 = field_name (str)
        # arg2 = nullable (bool)
        # arg3 = unique (bool)
        # arg4 = large_object (bool)
        current_buffer = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 5)
        validated_args = self.arg_validator.validate_args_type(
            args, ["java_type", "str", "bool", "bool", "bool"]
        )
        self.entity_field.create_basic_entity_field(
            current_buffer,
            *validated_args,
            debugger=True,
        )

    @command("GeneratedEnumEntityField", nargs="*")
    def generate_enum_entity_field(self, args) -> None:
        # arg0 = field_type (str)
        # arg1 = field_name (str)
        # arg2 = enum_type (ORDINAL | STRING)
        # arg3 = string_length (int)
        # arg4 = nullable (bool)
        # arg5 = unique (bool)
        current_buffer = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 6)
        validated_args = self.arg_validator.validate_args_type(
            args, ["str", "str", "enum", "int", "bool", "bool"]
        )
        self.entity_field.create_enum_entity_field(
            current_buffer,
            *validated_args,
            debugger=True,
        )
