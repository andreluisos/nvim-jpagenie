from pathlib import Path
from re import sub
from typing import Dict, List, Optional, Tuple

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

    @staticmethod
    def pluralize(word: str) -> str:
        if word.endswith(("s", "sh", "ch", "x", "z")):
            return word + "es"
        elif word.endswith("y") and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        elif word.endswith("f"):
            return word[:-1] + "ves"
        elif word.endswith("fe"):
            return word[:-2] + "ves"
        else:
            return word + "s"

    def proccess_collection_type(
        self, collection_type: str, debug: bool = False
    ) -> Tuple[str, str]:
        collection_name = collection_type.title()
        collection_initialization: str
        if collection_type == "set":
            collection_initialization = "new LinkedHashSet<>()"
        else:
            collection_initialization = "new ArrayList<>()"
        if debug:
            self.logging.log(
                [
                    f"Collection type: {collection_type}",
                    f"Collection name: {collection_name}",
                    f"Collection initialization: {collection_initialization}",
                ],
                "debug",
            )
        return (collection_name, collection_initialization)

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

    def process_cascades_params(
        self,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        debug: bool = False,
    ) -> Optional[str]:
        cascades: List[str] = []
        cascade_param: str
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
        if len(cascades) == 5:
            cascade_param = "cascade = CascadeType.ALL"
        elif len(cascades) == 1:
            cascade_param = f"cascade = CascadeType.{cascades[0]}"
        else:
            cascade_param = (
                f"cascade = {{{', '.join([f'CascadeType.{c}' for c in cascades])}}}"
            )
        if debug:
            self.logging.log(
                [
                    f"Persist: {cascade_persist}",
                    f"Merge: {cascade_merge}",
                    f"Remove: {cascade_remove}",
                    f"Refresh: {cascade_refresh}",
                    f"Detach: {cascade_detach}",
                    f"Cascades: {', '.join(cascades)}",
                    f"Cascade param: {cascade_param}",
                ],
                "debug",
            )

        return cascade_param

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

    def generate_many_to_one_one_side_annotation(
        self,
        one_field_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        debug: bool = False,
    ) -> str:
        body = "@OneToMany"
        cascade_param: Optional[str] = self.process_cascades_params(
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            debug,
        )
        params: List[str] = [
            f'mappedBy = "{self.generated_snaked_field_name(one_field_type)}"'
        ]
        if cascade_param:
            params.append(cascade_param)
        if orphan_removal:
            params.append("orphanRemoval = true")
        body += "(" + ", ".join(params) + ")"
        if debug:
            self.logging.log(
                [
                    f"Field type: {one_field_type}",
                    f"Field name: {params[0]}",
                    f"Params: {', '.join(params)}",
                    f"Orphan removal: {orphan_removal}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_many_to_one_many_side_annotation(
        self,
        one_fetch_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        nullable: bool,
        debug: bool = False,
    ):
        body = "@ManyToOne"
        cascade_param: Optional[str] = self.process_cascades_params(
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            debug,
        )
        params: List[str] = []
        if one_fetch_type != "none":
            params.append(f"fetch = FetchType.{one_fetch_type.upper()}")
        if cascade_param:
            params.append(cascade_param)
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
        return body

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
        return body

    def generate_many_to_one_many_side_field_body(
        self, field_type: str, debug: bool = False
    ) -> str:
        field_name = self.generate_field_name(field_type, False, debug)
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

    def generate_many_to_one_one_side_field_body(
        self,
        one_side_field_type: str,
        many_side_field_type: str,
        collection_type: str,
        debug: bool = False,
    ) -> str:
        one_side_field_name = self.generate_field_name(one_side_field_type, debug)
        many_side_field_name = self.generate_field_name(
            many_side_field_type, True, debug
        )
        collection: Tuple[str, str] = self.proccess_collection_type(
            collection_type, debug
        )
        body = f"private {collection[0]}<{many_side_field_type}> {many_side_field_name} = {collection[1]};"
        if debug:
            self.logging.log(
                [
                    f"One side field type: {one_side_field_type}",
                    f"One side field name: {one_side_field_name}",
                    f"Many side field type: {many_side_field_type}",
                    f"Many side field name: {many_side_field_name}",
                    f"Body:{body}",
                ],
                "debug",
            )
        return body

    def generate_many_to_one_one_side_template(
        self,
        one_side_field_type: str,
        many_side_field_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        collection_type: str,
        debug: bool = False,
    ) -> str:
        one_to_many_body = self.generate_many_to_one_one_side_annotation(
            one_side_field_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            orphan_removal,
            debug,
        )
        field_body = self.generate_many_to_one_one_side_field_body(
            one_side_field_type, many_side_field_type, collection_type, debug
        )
        body = "\n" + "\n" + one_to_many_body + "\n" + field_body + "\n"
        if debug:
            self.logging.log(body, "debug")
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
    ) -> str:
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
        field_body = self.generate_many_to_one_many_side_field_body(field_type, debug)
        complete_field_body = (
            "\n"
            + "\n"
            + many_to_one_body
            + "\n"
            + join_column_body
            + "\n"
            + field_body
            + "\n"
        )
        if debug:
            self.logging.log(complete_field_body, "debug")
        return complete_field_body

    def create_many_to_one_relationship(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        many_side_cascade_persist: bool,
        many_side_cascade_merge: bool,
        many_side_cascade_remove: bool,
        many_side_cascade_refresh: bool,
        many_side_cascade_detach: bool,
        fetch_type: str,
        mapping_type: str,
        nullable: bool,
        unique: bool,
        collection_type: str,
        orphan_removal: bool,
        one_side_cascade_persist: bool,
        one_side_cascade_merge: bool,
        one_side_cascade_remove: bool,
        one_side_cascade_refresh: bool,
        one_side_cascade_detach: bool,
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
        many_side_field_template = self.generate_many_to_one_many_side_template(
            field_type,
            fetch_type,
            many_side_cascade_persist,
            many_side_cascade_merge,
            many_side_cascade_remove,
            many_side_cascade_refresh,
            many_side_cascade_detach,
            nullable,
            unique,
            debug,
        )
        many_side_field_insert_point = (
            self.treesitter_lib.get_entity_field_insert_point(buffer_bytes, debug)
        )
        many_side_field_bytes = self.treesitter_lib.insert_code_into_position(
            many_side_field_template,
            many_side_field_insert_point,
            buffer_bytes,
            debug,
        )
        self.treesitter_lib.update_buffer(
            many_side_field_bytes, buffer_path, False, True, True, debug
        )
        if mapping_type == "bidirectional_joincolumn":
            one_side_buffer_bytes = self.treesitter_lib.get_bytes_from_path(
                one_side_field[1], debug
            )
            one_side_field_template = self.generate_many_to_one_one_side_template(
                one_side_field[0],
                many_side_field[0],
                one_side_cascade_persist,
                one_side_cascade_merge,
                one_side_cascade_remove,
                one_side_cascade_refresh,
                one_side_cascade_detach,
                orphan_removal,
                collection_type,
                debug,
            )
            one_side_field_insert_point = (
                self.treesitter_lib.get_entity_field_insert_point(
                    one_side_buffer_bytes, debug
                )
            )
            one_side_field_bytes = self.treesitter_lib.insert_code_into_position(
                one_side_field_template,
                one_side_field_insert_point,
                one_side_buffer_bytes,
                debug,
            )
            self.treesitter_lib.update_buffer(
                one_side_field_bytes, one_side_field[1], False, True, True, debug
            )
