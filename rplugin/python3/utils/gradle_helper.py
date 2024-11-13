from pynvim import Optional
from pynvim.api import Nvim
from custom_types.log_level import LogLevel
from custom_types.gradle_project_properties import (
    GradleProjectProperties,
)
from utils.common_utils import CommonUtils
from utils.treesitter_utils import TreesitterUtils
from utils.path_utils import PathUtils
from pathlib import Path
from platform import system
import subprocess
from utils.logging import Logging


class GradleHelper:
    def __init__(
        self,
        nvim: Nvim,
        cwd: Path,
        path_utils: PathUtils,
        treesitter_utils: TreesitterUtils,
        common_utils: CommonUtils,
        logging: Logging,
    ) -> None:
        self.nvim = nvim
        self.cwd = cwd
        self.logging = logging
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.common_utils = common_utils
        self.gradlew: Optional[Path] = None
        self.os_identifier = system()

    def get_gradle_file_path(self, debug: bool = False) -> Optional[Path]:
        project_root_path = self.path_utils.get_project_root_path()
        gradlew_file: Optional[Path] = None
        if self.os_identifier == "Windows":
            gradlew_file = next(project_root_path.glob("**/gradlew.bat"), None)
        else:
            gradlew_file = next(project_root_path.glob("**/gradlew"), None)
        self.gradlew = gradlew_file
        if debug:
            self.logging.log(
                [
                    f"Project's root path: {project_root_path}",
                    f"Operational system: {self.os_identifier}",
                    f"Gradlew file path: {gradlew_file}",
                ],
                LogLevel.DEBUG,
            )
        return gradlew_file

    def get_gradle_project_properties(
        self, debug: bool = False
    ) -> Optional[GradleProjectProperties]:
        project_properties: Optional[GradleProjectProperties] = None
        if self.gradlew:
            result = self.common_utils.run_subprocess(
                [f"{str(self.gradlew)}", "properties"], debug
            )
            project_name: Optional[str] = None
            project_version: Optional[str] = None
            project_group: Optional[str] = None
            project_build_dir: Optional[str] = None
            project_root_dir: Optional[str] = None
            project_dir: Optional[str] = None
            for line in result.stdout.splitlines():
                if line.startswith("name:"):
                    project_name = line.split(":")[1].strip()
                elif line.startswith("version:"):
                    project_version = line.split(":")[1].strip()
                elif line.startswith("group:"):
                    project_group = line.split(":")[1].strip()
                elif line.startswith("projectDir:"):
                    project_dir = line.split(":")[1].strip()
                elif line.startswith("rootDir:"):
                    project_root_dir = line.split(":")[1].strip()
                elif line.startswith("buildDir:"):
                    project_build_dir = line.split(":")[1].strip()

            if (
                project_name
                and project_group
                and project_version
                and project_build_dir
                and project_root_dir
                and project_dir
            ):
                project_properties = GradleProjectProperties(
                    project_name=project_name,
                    project_group=project_group,
                    project_version=project_version,
                    project_build_dir=project_build_dir,
                    project_root_dir=project_root_dir,
                    project_dir=project_dir,
                )
        if debug:
            self.logging.log(f"{project_properties}", LogLevel.DEBUG)
        return project_properties

    def get_project_executable(
        self, project_properties: GradleProjectProperties, debug: bool = False
    ) -> Optional[Path]:
        executable_path = next(
            project_properties.project_build_path.glob(
                f"**/{project_properties.project_name}-{project_properties.project_version}.jar"
            ),
            None,
        )
        if debug:
            self.logging.log(f"Executable path: {executable_path}", LogLevel.DEBUG)
        return executable_path

    def gradle_build(self) -> None:
        self.logging.echomsg("Building")
        output: Optional[str] = None
        error: Optional[str] = None
        try:
            result = self.common_utils.run_subprocess([f"{str(self.gradlew)}", "build"])
            output = " ".join(result.stdout.splitlines())
            error = " ".join(result.stderr.splitlines())
            if output and "BUILD SUCCESSFUL" in output:
                self.logging.echomsg("Build successful")
        except subprocess.CalledProcessError as e:
            output = " ".join(e.stdout.splitlines()) if e.stdout else None
            error = " ".join(e.stderr.splitlines()) if e.stderr else None
        except Exception as e:
            error = str(e)
            error_msg = f"Unexpected error: {error}"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)

    def gradle_run(self, debug: bool = False) -> None:
        self.get_gradle_file_path(debug)
        self.gradle_build()
        project_properties = self.get_gradle_project_properties(debug)
        if not project_properties:
            error_msg = "Unable to get project's properties"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        project_executable = self.get_project_executable(project_properties)
        if not project_executable:
            error_msg = "Unable to find built executable"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        java_executable = self.path_utils.get_java_executable_path()
        self.nvim.command(
            f"split | terminal {str(java_executable)} -jar {str(project_executable)}"
        )
