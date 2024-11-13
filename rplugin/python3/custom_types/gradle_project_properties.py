from dataclasses import dataclass, field, InitVar
from pathlib import Path


@dataclass
class GradleProjectProperties:
    project_name: str
    project_group: str
    project_version: str
    project_build_dir: InitVar[str]
    project_dir: InitVar[str]
    project_root_dir: InitVar[str]
    project_build_path: Path = field(init=False)
    project_path: Path = field(init=False)
    project_root_path: Path = field(init=False)

    def __post_init__(
        self, project_build_dir: str, project_dir: str, project_root_dir: str
    ):
        self.project_build_path = Path(project_build_dir)
        self.project_path = Path(project_dir)
        self.project_root_path = Path(project_root_dir)
