from typing import Dict, List
from pynvim import plugin, command, function
from pynvim.api import Nvim

from base import Base
from custom_types.log_level import LogLevel
from custom_types.create_java_file_args import CreateJavaFileArgs


@plugin
class JavaFileCreationCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)
        self.debug: bool = False

    @command("CreateNewJavaFile", nargs="*")
    def create_java_file(self, args: List[str]) -> None:
        self.logging.reset_log_file()
        if len(args) > 1:
            error_msg = "Only one arg is allowed"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        self.debug = True if "debug" in args else False
        root_package_path = str(self.path_utils.get_spring_root_package_path(True))
        self.nvim.exec_lua(
            self.common_utils.read_ui_file_as_string("create_java_file.lua"),
            (
                self.ui_path,
                root_package_path,
            ),
        )

    @function("CreateNewJavaFileCallback")
    def create_new_java_file_callback(self, args: List[Dict]):
        converted_args = CreateJavaFileArgs(**args[0])
        if self.debug:
            self.logging.log(f"Converted args: {converted_args}", LogLevel.DEBUG)
        self.java_file_utils.create_java_file(
            args=converted_args,
            debug=self.debug,
        )
