from pathlib import Path

from pynvim import command

from coreutils import Util


class Command(Util):
    def __init__(self, nvim):
        super().__init__(nvim)

    @command("CreateJavaFile", nargs=3)
    def create_java_file(self, args: list[str]) -> None:
        package_path: str = args[0]
        name: str = args[1]
        type: str = args[2]
        if type not in ["class", "interface", "record", "enum", "annotation"]:
            self.nvim.command("echo 'Invalid file type'")
            return
        file_path = self.get_spring_main_class_path()
        if file_path is None:
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
        base_path = Path(file_path).parent
        relative_path = Path(package_path.replace(".", "/"))
        file_path = base_path / relative_path / f"{name}.java"
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
            self.nvim.command(f"echo 'File {file_path} created'")
        else:
            self.nvim.command(f"echo 'File {file_path} already exists'")
