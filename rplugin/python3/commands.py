from pathlib import Path

from pynvim import command, plugin

from coreutils import Util


@plugin
class Command(object):
    def __init__(self, nvim):
        self.nvim = nvim
        self.cwd = Path(self.nvim.funcs.getcwd()).resolve()
        self.util = Util(self.cwd)

    @command("CreateJavaFile", nargs="*")
    def create_java_file(self, args) -> None:
        if len(args) != 3:
            self.nvim.command("echo 'Invalid number of arguments. Expected 3.'")
            return
        package_path: str = args[0]
        name: str = args[1]
        type: str = args[2]
        if type not in ["class", "interface", "record", "enum", "annotation"]:
            self.nvim.command("echo 'Invalid file type'")
            return
        main_class_path = self.util.get_spring_main_class_path()
        if main_class_path is None:
            self.nvim.command("echo 'Spring main class path not found'")
            return
        boiler_plate: str = ""
        if type in ["class", "interface", "enum"]:
            boiler_plate = (
                f"""package {package_path};\n\npublic {type} {name} {{\n\n}}"""
            )
        elif type == "record":
            boiler_plate = (
                f"""package {package_path};\n\npublic record {name}(\n\n) {{}}"""
            )
        else:
            boiler_plate = (
                f"""package {package_path};\n\npublic @interface {name} {{\n\n}}"""
            )
        base_path = Path(main_class_path).parent
        relative_path = Path(package_path.replace(".", "/"))
        index_to_replace: int
        try:
            index_to_replace = base_path.parts.index("main") + 1
        except ValueError:
            self.nvim.command("echo 'Unable to parse root directory.")
            return
        file_path = (
            Path(*base_path.parts[:index_to_replace]) / relative_path / f"{name}.java"
        )
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
                self.nvim.command(f"echo 'File {file_path} created'")
        else:
            self.nvim.command(f"echo 'File {file_path} already exists'")
