from typing import List
from pynvim.api import Nvim
from lib.treesitterlib import TreesitterLib
from pathlib import Path

from lib.pathlib import PathLib
from util.logging import Logging


class CommonHelper:
    def __init__(
        self,
        nvim: Nvim,
        cwd: Path,
        treesitter_lib: TreesitterLib,
        path_lib: PathLib,
        logging: Logging,
    ) -> None:
        self.nvim = nvim
        self.cwd = cwd
        self.treesitter_lib = treesitter_lib
        self.logging = logging
        self.path_lib = path_lib

    def add_imports_to_buffer(
        self, import_list: List[str], buffer_bytes: bytes, debug: bool
    ) -> bytes:
        updated_buffer_bytes = self.treesitter_lib.insert_import_paths_into_buffer(
            buffer_bytes, import_list, debug
        )
        import_list = []
        return updated_buffer_bytes

    def pluralize(self, word: str, debug: bool = False) -> str:
        pluralized_word: str
        if word.endswith(("s", "sh", "ch", "x", "z")):
            pluralized_word = word + "es"
        elif word.endswith("y") and word[-2] not in "aeiou":
            pluralized_word = word[:-1] + "ies"
        elif word.endswith("f"):
            pluralized_word = word[:-1] + "ves"
        elif word.endswith("fe"):
            pluralized_word = word[:-2] + "ves"
        else:
            pluralized_word = word + "s"
        if debug:
            self.logging.log(
                [f"Word: {word}", f"Pluralized word: {pluralized_word}"], "debug"
            )
        return pluralized_word

    def generate_field_name(
        self, field_type: str, plural: bool = False, debug: bool = False
    ) -> str:
        field_name = field_type
        if plural:
            field_name = self.pluralize(field_name)
        field_name = field_name[0].lower() + field_name[1:]
        if debug:
            self.logging.log(
                [f"Field type: {field_type}", f"Field name: {field_name}"], "debug"
            )
        return field_name
