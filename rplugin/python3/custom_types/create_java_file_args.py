from dataclasses import dataclass, field, InitVar
from custom_types.java_file_type import JavaFileType


@dataclass
class CreateJavaFileArgs:
    package_path: str
    file_name: str
    file_type: InitVar[str]
    file_type_enum: JavaFileType = field(init=False)

    def __post_init__(
        self,
        file_type: str,
    ):
        self.file_type_enum = JavaFileType.from_value(file_type)
