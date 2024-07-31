from pathlib import Path
from typing import Literal

from echomsg import EchoMsg


class CreateJavaFile:
    def __init__(self, nvim, echomsg: EchoMsg):
        self.nvim = nvim
        self.echomsg = echomsg

    def create_java_file(
        self,
        main_class_path: str,
        package_path: str,
        file_name: str,
        file_type: Literal["class", "interface", "record", "enum", "annotation"],
    ) -> None:
        boiler_plate: str = ""
        if file_type in ["class", "interface", "enum"]:
            boiler_plate = f"""package {package_path};\n\npublic {file_type} {file_name} {{\n\n}}"""
        elif file_type == "record":
            boiler_plate = (
                f"""package {package_path};\n\npublic record {file_name}(\n\n) {{}}"""
            )
        else:
            boiler_plate = (
                f"""package {package_path};\n\npublic @interface {file_name} {{\n\n}}"""
            )
        base_path = Path(main_class_path).parent
        relative_path = Path(package_path.replace(".", "/"))
        index_to_replace: int
        try:
            index_to_replace = base_path.parts.index("main") + 1
        except ValueError:
            self.echomsg.print("Unable to parse root directory.")
            return
        file_path = (
            Path(*base_path.parts[:index_to_replace])
            / relative_path
            / f"{file_name}.java"
        )
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
                self.echomsg.print(f"File {file_path} created")
        else:
            self.echomsg.print(f"File {file_path} already exists")
