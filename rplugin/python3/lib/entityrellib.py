from pathlib import Path
from re import sub
from typing import Dict, List, Tuple

from lib.pathlib import PathLib
from lib.treesitterlib import TreesitterLib
from pynvim.api.nvim import Nvim
from util.logging import Logging


class EntityRelationshipLib:
    def __init__(
        self,
        nvim: Nvim,
        treesitter_lib: TreesitterLib,
        path_lib: PathLib,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_lib = treesitter_lib
        self.path_lib = path_lib
        self.logging = logging

    def get_all_jpa_entities(self, debug: bool = False) -> Dict[str, Path]:
        root_path = Path(self.path_lib.get_spring_project_root_path())
        entities_found: Dict[str, Path] = {}
        for p in root_path.rglob("*.java"):
            if self.treesitter_lib.is_buffer_jpa_entity(p, debug):
                entity_path = p
                entity_node = self.treesitter_lib.get_node_from_path(p, debug)
                entity_name = self.treesitter_lib.get_node_class_name(
                    entity_node, debug
                )
                if entity_name:
                    entities_found[entity_name] = entity_path
        if debug:
            self.logging.log(
                [f"{e[0]} - {str(e[1])}" for e in entities_found.items()], "debug"
            )
        return entities_found

    def generate_field_name(self, field_type: str, debug: bool = False) -> str:
        field_name = field_type[0].lower() + field_type[1:]
        if debug:
            self.logging.log(
                [f"Field type: {field_type}", f"Field name: {field_name}"], "debug"
            )
        return field_name

    def generated_snaked_field_name(self, field_type: str, debug: bool = False) -> str:
        snaked_field_name = sub(r"(?<!^)(?=[A-Z])", "_", field_type).lower() + "_id"
        if debug:
            self.logging.log(
                [
                    f"Field type: {field_type}",
                    f"Snaked field name: {snaked_field_name}",
                ],
                "debug",
            )
        return snaked_field_name

    def generate_many_to_one_many_side_annotation(
        self,
        fetch_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        nullable: bool,
        debug: bool = False,
    ):
        body = "@ManyToOne"
        cascades: List[str] = []
        params: List[str] = []
        if cascade_persist:
            cascades.append("PERSIST")
        if cascade_merge:
            cascades.append("MERGE")
        if cascade_remove:
            cascades.append("REMOVE")
        if cascade_refresh:
            cascades.append("REFRESH")
        if cascade_detach:
            cascades.append("DETACH")
        if fetch_type != "none":
            params.append(f"fetch = FetchType.{fetch_type.upper()}")
        if len(cascades) == 5:
            params.append("cascade = CascadeType.ALL")
        elif len(cascades) == 1:
            params.append(f"cascade = CascadeType.{cascades[0]}")
        else:
            params.append(
                f"cascade = {{{', '.join([f'CascadeType.{c}' for c in cascades])}}}"
            )
        if len(params) > 0:
            body += "(" + ", ".join(params) + ")"
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Optional: {nullable}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body + "\n"

    def generate_join_column_many_side_annotation(
        self, field_type: str, nullable: bool, unique: bool, debug: bool = False
    ) -> str:
        body = "@JoinColumn("
        snaked_field_name = self.generated_snaked_field_name(field_type, debug)
        body += f'name = "{snaked_field_name}"'
        if nullable:
            body += ", nullable = true"
        if unique:
            body += ", unique = true"
        body += ")"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {field_type}",
                    f"Nullable: {nullable}",
                    f"Unique: {unique}",
                ],
                "debug",
            )
        return body + "\n"

    def generate_field_body(self, field_type: str, debug: bool = False) -> str:
        field_name = self.generate_field_name(field_type, debug)
        body = f"private {field_type} {field_name};"
        if debug:
            self.logging.log(
                [
                    f"Field type: {field_type}",
                    f"Field name: {field_name}",
                    f"Field body: {body}",
                ],
                "debug",
            )
        return body

    def generate_many_to_one_many_side_template(
        self,
        field_type: str,
        fetch_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        nullable: bool,
        unique: bool,
        debug: bool = False,
    ):
        many_to_one_body = self.generate_many_to_one_many_side_annotation(
            fetch_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            nullable,
            debug,
        )
        join_column_body = self.generate_join_column_many_side_annotation(
            field_type, nullable, unique, debug
        )
        field_body = self.generate_field_body(field_type, debug)
        complete_field_body = (
            "\n" + many_to_one_body + join_column_body + field_body + "\n"
        )
        if debug:
            self.logging.log(complete_field_body, "debug")
        return complete_field_body

    def create_many_to_one_relationship(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        fetch_type: str,
        mapping_type: str,
        nullable: bool,
        unique: bool,
        debug: bool = False,
    ):
        all_entities = self.get_all_jpa_entities(debug)
        one_side_field: Tuple[str, Path] | None = None
        many_side_field: Tuple[str, Path] | None = None
        for entity in all_entities:
            entity_path = all_entities[entity]
            if buffer_path == entity_path:
                many_side_field = (entity, entity_path)
            if entity == field_type:
                one_side_field = (entity, entity_path)
        if not one_side_field:
            error_msg = f"{field_type} is not a valid entity"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        if not many_side_field:
            error_msg = "Couldn't process currenty entity"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        one_side_buffer_bytes = self.treesitter_lib.get_bytes_from_path(
            one_side_field[1]
        )
        many_side_field_bytes = self.treesitter_lib.get_bytes_from_path(
            many_side_field[1]
        )
        many_side_field_template = self.generate_many_to_one_many_side_template(
            field_type,
            fetch_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            nullable,
            unique,
            debug,
        )
        many_side_field_insert_point = (
            self.treesitter_lib.get_entity_field_insert_point(
                many_side_field_bytes, debug
            )
        )
        many_side_field_bytes = self.treesitter_lib.insert_code_into_position(
            many_side_field_template,
            many_side_field_insert_point,
            many_side_field_bytes,
            debug,
        )
        self.treesitter_lib.update_buffer(
            many_side_field_bytes, many_side_field[1], False, True, True, debug
        )
