from pathlib import Path
from typing import Literal
from pynvim.api.nvim import Nvim
from pynvim.plugin import command, plugin

from echomsg import EchoMsg

from createjavafile import CreateJavaFile
from coreutils import Util


@plugin
class Command(object):
    def __init__(self, nvim: Nvim) -> None:
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.util = Util(self.cwd)
        self.echomsg = EchoMsg(nvim)
        self.java_file = CreateJavaFile(self.nvim, self.echomsg)

    @command("CreateJavaFile", nargs="*")
    def create_java_file(self, args) -> None:
        if len(args) != 3:
            self.echomsg.print("Invalid number of arguments. Expected 3.")
            return
        package_path: str = args[0]
        file_name: str = args[1]
        file_type: Literal["class", "interface", "record", "enum", "annotation"] = args[
            2
        ]
        main_class_path = self.util.get_spring_main_class_path()
        if main_class_path is None:
            self.echomsg.print("Spring main class path not found")
            return
        self.java_file.create_java_file(
            main_class_path=main_class_path,
            package_path=package_path,
            file_name=file_name,
            file_type=file_type,
        )
