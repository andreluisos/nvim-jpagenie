from pathlib import Path

from pynvim.api import Buffer
from pynvim.api.nvim import Nvim
from pynvim.plugin import command, plugin

from constants.typing import JAVA_BASIC_TYPES
from lib.entityfieldlib import EntityFieldLib
from lib.javafilelib import JavaFileLib
from lib.jparepolib import JpaRepositoryLib
from lib.pathlib import PathLib
from lib.treesitterlib import TreesitterLib
from util.argvalidator import ArgValidator
from util.logging import Logging


@plugin
class Base(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.java_basic_types = JAVA_BASIC_TYPES
        self.logging = Logging(nvim)
        self.arg_validator = ArgValidator(self.java_basic_types, self.logging)
        self.treesitter_lib = TreesitterLib(
            self.nvim, self.java_basic_types, self.cwd, self.logging
        )
        self.path_lib = PathLib(self.cwd, self.treesitter_lib, self.logging)
        self.java_file_lib = JavaFileLib(self.nvim, self.logging)
        self.jpa_repo_lib = JpaRepositoryLib(
            self.nvim, self.treesitter_lib, self.path_lib, self.logging
        )
        self.entity_field_lib = EntityFieldLib(
            self.nvim, self.java_basic_types, self.treesitter_lib, self.logging
        )

    @command("JavaFileLib", nargs="*")
    def create_java_file_lib(self, args) -> None:
        # arg0 = package_path (str)
        # arg1 = file_name (str)
        # arg2 = file_type (java_file_lib)
        self.arg_validator.validate_args_length(args, 3)
        validated_args = self.arg_validator.validate_args_type(
            args, ["str", "str", "java_file_lib"]
        )
        main_class_path = self.path_lib.get_spring_main_class_path()
        self.java_file_lib.create_java_file(
            main_class_path,
            *validated_args,
            debugger=True,
        )

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

    @command("GenerateBasicEntityField", nargs="*")
    def generate_basic_entity_field_lib(self, args) -> None:
        # arg0 = field_type (java_type)
        # arg1 = field_name (str)
        # arg2 = nullable (bool)
        # arg3 = unique (bool)
        # arg4 = large_object (bool)
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 5)
        validated_args = self.arg_validator.validate_args_type(
            args, ["java_type", "str", "bool", "bool", "bool"]
        )
        self.entity_field_lib.create_basic_entity_field(
            buffer_bytes,
            buffer_path,
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
        current_buffer: Buffer = self.nvim.current.buffer
        buffer_bytes = self.treesitter_lib.get_bytes_from_buffer(current_buffer)
        buffer_path = Path(self.nvim.current.buffer.name)
        self.arg_validator.validate_args_length(args, 6)
        validated_args = self.arg_validator.validate_args_type(
            args, ["str", "str", "enum", "int", "bool", "bool"]
        )
        self.entity_field_lib.create_enum_entity_field(
            buffer_bytes,
            buffer_path,
            *validated_args,
            debugger=True,
        )
