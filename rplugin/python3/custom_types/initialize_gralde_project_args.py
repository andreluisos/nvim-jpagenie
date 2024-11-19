from dataclasses import dataclass
from typing import Literal


@dataclass
class InitializeGradleProjectArgs:
    project_name: str
    project_package: str
    project_path: str
    project_type: Literal["java-application"]
    java_version: Literal[
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
    ]
    gradle_dsl: Literal["kotlin", "groovy"]
    comments: bool
