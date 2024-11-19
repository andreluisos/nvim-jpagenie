from platform import system
from zipfile import ZipFile
from tempfile import TemporaryDirectory
from urllib import request
from json import load
from typing import Dict, List
from pynvim import Optional
from pynvim.api import Nvim
from custom_types.log_level import LogLevel
from custom_types.initialize_gralde_project_args import (
    InitializeGradleProjectArgs,
)
from utils.common_utils import CommonUtils
from utils.treesitter_utils import TreesitterUtils
from utils.path_utils import PathUtils
from pathlib import Path
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
        self.gradle_base_path: Path = (
            self.path_utils.get_plugin_base_path().joinpath("bin").joinpath("gradle")
        )

    def get_gradle_release_tags(self, debug: bool = False) -> List[str]:
        request_result: List[Dict] = []
        tags: List[str] = []
        with request.urlopen(
            "https://api.github.com/repos/gradle/gradle/tags"
        ) as response:
            request_result = load(response)
        if request_result is not None:
            for tag in request_result:
                if "-" not in tag["name"]:
                    tags.append(tag["name"])
        if debug:
            self.logging.log(tags, LogLevel.DEBUG)
        return tags

    def get_clean_tag(self, tag: str, debug: bool = False) -> str:
        clean_tag = tag[1:]
        if len(clean_tag.split(".")) >= 3 and clean_tag[-1] == "0":
            clean_tag = clean_tag[:-2]
        if debug:
            self.logging.log(f"Clean tag: {clean_tag}", LogLevel.DEBUG)
        return clean_tag

    def get_gradle_binary_path(
        self, clean_tag: str, debug: bool = False
    ) -> Optional[Path]:
        # TODO: check for existing gradle system installation
        bin_path: Optional[Path] = None
        bin_base_path = self.gradle_base_path.joinpath(f"gradle-{clean_tag}").joinpath(
            "bin"
        )
        if bin_base_path.exists():
            if system() == "Windows":
                bin_path = bin_base_path.joinpath("gradle.bat")
            bin_path = bin_base_path.joinpath("gradle")
        if debug:
            self.logging.log(
                [f"Bin base path: {bin_base_path}", f"Bin path: {bin_path}"],
                LogLevel.DEBUG,
            )
        return bin_path

    def download_gradle_binary(self, clean_tag: str, debug: bool = False) -> None:
        gradle_binary_path = self.get_gradle_binary_path(clean_tag, debug)
        if gradle_binary_path and gradle_binary_path.exists():
            if debug:
                self.logging.log(
                    f"Gradle binary already exists at {gradle_binary_path}",
                    LogLevel.DEBUG,
                )
            return
        try:
            with TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                zip_path = temp_dir_path / f"gradle-{clean_tag}-bin.zip"
                url = f"https://services.gradle.org/distributions/gradle-{clean_tag}-bin.zip"
                self.logging.echomsg(f"Downloading Gradle {clean_tag} from {url}")
                with request.urlopen(url) as response, open(zip_path, "wb") as out_file:
                    data = response.read()
                    out_file.write(data)
                if debug:
                    self.logging.log(
                        f"Downloaded Gradle binary to {zip_path}", LogLevel.DEBUG
                    )
                with ZipFile(zip_path, "r") as zip_ref:
                    self.gradle_base_path.mkdir(parents=True, exist_ok=True)
                    zip_ref.extractall(self.gradle_base_path)
                    if debug:
                        self.logging.log(
                            f"Extracted all files to {self.gradle_base_path}",
                            LogLevel.DEBUG,
                        )
                gradle_bin_path = self.get_gradle_binary_path(clean_tag, debug)
                if gradle_bin_path and gradle_bin_path.exists():
                    gradle_bin_path.chmod(gradle_bin_path.stat().st_mode | 0o111)
                    if debug:
                        self.logging.log(
                            f"Set executable permission on {gradle_bin_path}",
                            LogLevel.DEBUG,
                        )
        except Exception as e:
            error_msg = f"Failed to download or extract Gradle binary: {str(e)}"
            self.logging.echomsg(error_msg)
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)

    def initialize_gradle_project(
        self,
        gradle_tag: Optional[str],
        args: InitializeGradleProjectArgs,
        debug: bool = False,
    ) -> None:
        clean_gradle_tag: Optional[str] = None
        if not gradle_tag:
            gradle_tag = self.get_gradle_release_tags(debug)[0]
        clean_gradle_tag = self.get_clean_tag(gradle_tag, debug)
        gradle_binary_path = self.get_gradle_binary_path(clean_gradle_tag, debug)
        if not gradle_binary_path:
            self.download_gradle_binary(clean_gradle_tag)
            gradle_binary_path = self.get_gradle_binary_path(clean_gradle_tag, debug)
        project_path = Path(args.project_path)
        if not project_path.exists():
            project_path.mkdir(parents=True, exist_ok=True)
        else:
            error_msg = f"{project_path} is not empty"
            self.logging.log(error_msg, LogLevel.DEBUG)
            raise RuntimeError(error_msg)
        cmd = [
            str(gradle_binary_path),
            "init",
            "--type",
            args.project_type,
            "--dsl",
            args.gradle_dsl,
            "--project-dir",
            args.project_path,
            "--project-name",
            args.project_name,
            "--package",
            args.project_package,
            "--java-version",
            args.java_version,
            "--test-framework",
            "junit-jupiter",
            "--use-defaults",
            "--no-comments",
        ]
        self.common_utils.run_subprocess(cmd)
        project_main_class_path = self.path_utils.get_java_project_main_class(
            project_path
        )
        self.nvim.command(f":e {project_main_class_path}")
