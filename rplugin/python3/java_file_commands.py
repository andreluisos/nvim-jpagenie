from pynvim import plugin
from pynvim.api import Nvim
from pynvim.plugin import command

from base import Base


@plugin
class JavaFileCommands(Base):
    def __init__(self, nvim: Nvim) -> None:
        super().__init__(nvim)

    @command("CreateJavaFile", nargs="*")
    def create_java_file_lib(self, args: List[str]) -> None:
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
            debug=attach_debugger,
        )
