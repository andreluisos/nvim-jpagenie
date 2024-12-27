from typing import Literal
from pynvim import Optional
from pynvim.api import Nvim
from custom_types.log_level import LogLevel
from custom_types.project_properties import ProjectProperties
from utils.common_utils import CommonUtils
from utils.treesitter_utils import TreesitterUtils
from utils.path_utils import PathUtils
from pathlib import Path
from platform import system
import subprocess
from utils.logging import Logging


class BuildHelper:
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
        self.build_tool_type: Optional[Literal["maven", "gradle"]] = None
        self.build_tool_path: Optional[Path] = self.get_build_tool_file_path()

    def get_build_tool_file_path(self) -> Path:
        os_identifier = system()
        project_root_path = self.path_utils.get_project_root_path()
        gradlew_file: Optional[Path] = None
        maven_file: Optional[Path] = None
        gradlew_file = next(
            project_root_path.glob(
                "**/gradlew.bat" if os_identifier == "Windows" else "**/gradlew"
            ),
            None,
        )
        if gradlew_file:
            self.build_tool_type = "gradle"
            return gradlew_file
        maven_file = next(
            project_root_path.glob(
                "**/mvnw.bat" if os_identifier == "Windows" else "**/mvnw"
            ),
            None,
        )
        if maven_file:
            self.build_tool_type = "maven"
            return maven_file
        error_msg = "Unable to get build tool"
        self.logging.log(error_msg, LogLevel.ERROR)
        raise FileNotFoundError(error_msg)

    def get_maven_project_properties(
        self, debug: bool = False
    ) -> Optional[ProjectProperties]:
        project_properties: Optional[ProjectProperties] = None
        if self.build_tool_type == "maven":
            result = self.common_utils.run_subprocess(
                [
                    f"{str(self.build_tool_path)}",
                    "help:evaluate",
                    "-Dexpression=project.name",
                    "-q",
                    "-DforceStdout",
                ],
                debug,
            )
            project_name = result.stdout.strip()

            result = self.common_utils.run_subprocess(
                [
                    f"{str(self.build_tool_path)}",
                    "help:evaluate",
                    "-Dexpression=project.version",
                    "-q",
                    "-DforceStdout",
                ],
                debug,
            )
            project_version = result.stdout.strip()

            result = self.common_utils.run_subprocess(
                [
                    f"{str(self.build_tool_path)}",
                    "help:evaluate",
                    "-Dexpression=project.groupId",
                    "-q",
                    "-DforceStdout",
                ],
                debug,
            )
            project_group = result.stdout.strip()

            project_build_dir = str(self.cwd / "target")
            project_root_dir = str(self.cwd)
            project_dir = str(self.cwd)

            if project_name and project_group and project_version:
                project_properties = ProjectProperties(
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

    def get_gradle_project_properties(
        self, debug: bool = False
    ) -> Optional[ProjectProperties]:
        project_properties: Optional[ProjectProperties] = None
        if self.build_tool_path and self.build_tool_type == "gradle":
            result = self.common_utils.run_subprocess(
                [f"{str(self.build_tool_path)}", "properties"], debug
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
                project_properties = ProjectProperties(
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
        self, project_properties: ProjectProperties, debug: bool = False
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

    def maven_build(self) -> None:
        self.logging.echomsg("Building")
        output: Optional[str] = None
        error: Optional[str] = None
        try:
            result = self.common_utils.run_subprocess(
                [f"{str(self.build_tool_path)}", "package"]
            )
            output = " ".join(result.stdout.splitlines())
            error = " ".join(result.stderr.splitlines())
            if output and "BUILD SUCCESS" in output:
                self.logging.echomsg("Build successful")
            if "BUILD SUCCESS" not in output:
                error_msg = "Unable to build"
                self.logging.log(error_msg, LogLevel.ERROR)
                raise ValueError(error_msg)
        except subprocess.CalledProcessError as e:
            output = " ".join(e.stdout.splitlines()) if e.stdout else None
            error = " ".join(e.stderr.splitlines()) if e.stderr else None
        except Exception as e:
            error = str(e)
            error_msg = f"Unexpected error: {error}"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)

    def gradle_build(self) -> None:
        self.logging.echomsg("Building")
        output: Optional[str] = None
        error: Optional[str] = None
        try:
            result = self.common_utils.run_subprocess(
                [f"{str(self.build_tool_path)}", "build", "-x", "tests"]
            )
            output = " ".join(result.stdout.splitlines())
            error = " ".join(result.stderr.splitlines())
            if output and "BUILD SUCCESSFUL" in output:
                self.logging.echomsg("Build successful")
            if "BUILD SUCCESSFUL" not in output:
                error_msg = "Unable to build"
                self.logging.log(error_msg, LogLevel.ERROR)
                raise ValueError(error_msg)
        except subprocess.CalledProcessError as e:
            output = " ".join(e.stdout.splitlines()) if e.stdout else None
            error = " ".join(e.stderr.splitlines()) if e.stderr else None
        except Exception as e:
            error = str(e)
            error_msg = f"Unexpected error: {error}"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)

    def run(self, debug: bool = False) -> None:
        if self.build_tool_type == "gradle":
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
        else:
            self.maven_build()
            project_properties = self.get_maven_project_properties(debug)
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
