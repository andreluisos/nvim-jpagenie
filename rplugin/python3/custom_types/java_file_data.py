from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Tree

from custom_types.declaration_type import DeclarationType


@dataclass
class JavaFileData:
    package_path: str
    file_name: str
    path: Path
    tree: Tree
    declaration_type: DeclarationType
    is_jpa_entity: bool

    def print(self) -> str:
        repr = (
            f"EntityData("
            f"package_path='{self.package_path}', "
            f"file_name='{self.file_name}', "
            f"path='{str(self.path)}', "
            f"declaration_type='{self.declaration_type}', "
            f"is_jpa_entity='{self.is_jpa_entity}'"
            f")"
        )
        # Escape single quotes for Vim
        repr = repr.replace("'", "''")
        return repr
