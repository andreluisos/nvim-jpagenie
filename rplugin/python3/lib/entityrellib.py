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

    def process_extra_params(
        self,
        nullable: Optional[bool] = None,
        optional: Optional[bool] = None,
        unique: Optional[bool] = None,
        orphan_removal: Optional[bool] = None,
        fetch: Optional[str] = None,
        name: Optional[str] = None,
        mapped_by: Optional[str] = None,
        debug: bool = False,
    ) -> str:
        params: List[str] = []
        if name is not None:
            params.append(f'name = "{name}"')
        if mapped_by is not None:
            params.append(f'mappedBy = "{mapped_by}"')
        if nullable is not None:
            params.append(f"nullable = {str(nullable).lower()}")
        if optional is not None:
            params.append(f"optional = {str(optional).lower()}")
        if unique is not None:
            params.append(f"unique = {str(unique).lower()}")
        if orphan_removal is not None:
            params.append(f"orphanRemoval = {str(orphan_removal).lower()}")
        if fetch is not None:
            params.append(f"fetch = FetchType.{fetch.upper()}")
        joined_params = ", ".join(params)
        if debug:
            self.logging.log(
                [
                    f"Nullable: {nullable}",
                    f"Optional: {optional}",
                    f"Orphan removal: {orphan_removal}",
                    f"Fetch: {fetch}",
                    f"Name: {name}",
                    f"MappedBy: {mapped_by}",
                    f"Params body: {joined_params}",
                ],
                "debug",
            )
        return joined_params

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

    def get_bidirectional_buffer_data(
        self,
        owning_side_buffer_path: Path,
        inverse_side_type: str,
        debug: bool = False,
    ) -> Dict[str, Tuple[str, Path]]:
        all_entities = self.get_all_jpa_entities(debug)
        related_entities: Dict[str, Tuple[str, Path]] = {}
        for entity in all_entities:
            entity_path = all_entities[entity]
            if owning_side_buffer_path == entity_path:
                related_entities["owning_side"] = (entity, entity_path)
            if entity == inverse_side_type:
                related_entities["inverse_side"] = (entity, entity_path)
        if debug:
            self.logging.log(f"Buffer data: {str(related_entities)}", "debug")
        if "owning_side" not in related_entities:
            error_msg = f"{related_entities['inverse_side']} is not a valid entity"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        if "inverse_side" not in related_entities:
            error_msg = "Couldn't process currenty entity"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        return related_entities

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

    def generate_one_to_many_annotation_body(
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
        params: List[str] = []
        cascade_param: Optional[str] = self.process_cascades_params(
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            debug,
        )
        extra_params: str = self.process_extra_params(
            orphan_removal=True,
            mapped_by=self.generated_snaked_field_name(one_field_type),
            debug=debug,
        )
        params.append(extra_params)
        if cascade_param:
            params.append(cascade_param)
        if len(params) > 0:
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

    def generate_many_to_one_annotation_body(
        self,
        fetch_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        optional: bool,
        debug: bool = False,
    ):
        body = "@ManyToOne"
        params: List[str] = []
        cascade_param: Optional[str] = self.process_cascades_params(
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            debug,
        )
        extra_params: str = self.process_extra_params(
            fetch=fetch_type if fetch_type != "none" else None,
            optional=optional,
            debug=debug,
        )
        params.append(extra_params)
        if cascade_param:
            params.append(cascade_param)
        if len(params) > 0:
            body += "(" + ", ".join(params) + ")"
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Optional: {optional}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_join_column_body(
        self,
        inverse_side_field_type: str,
        nullable: bool,
        unique: bool,
        debug: bool = False,
    ) -> str:
        body = "@JoinColumn"
        snaked_field_name = self.generated_snaked_field_name(
            inverse_side_field_type, debug
        )
        extra_params = self.process_extra_params(
            name=snaked_field_name, nullable=nullable, unique=unique, debug=debug
        )
        body += "(" + extra_params + ")"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {inverse_side_field_type}",
                    f"Nullable: {nullable}",
                    f"Unique: {unique}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_field_body(
        self,
        field_type: str,
        is_collection: bool,
        collection_type: Optional[str],
        debug: bool = False,
    ) -> str:
        collection_name: str = ""
        if is_collection and collection_type:
            collection_name = collection_type.title()
        field_name = self.generate_field_name(
            field_type, True if is_collection else False, debug
        )
        body = (
            f"private {collection_name}"
            f"{'<' if is_collection else ''}{field_type}{'>' if is_collection else ''} "
            f"{field_name};"
        )
        if debug:
            self.logging.log(
                [
                    f"Field type: {field_type}",
                    f"Field name: {field_name}",
                    f"Is collection: {is_collection}",
                    f"Collection type: {collection_type}",
                    f"Field body: {body}",
                ],
                "debug",
            )
        return body

    def generate_one_to_many_template(
        self,
        owning_side_field_type: str,
        inverse_side_field_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        collection_type: str,
        debug: bool = False,
    ) -> str:
        one_to_many_body = self.generate_one_to_many_annotation_body(
            inverse_side_field_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            orphan_removal,
            debug,
        )
        field_body = self.generate_field_body(
            owning_side_field_type, True, collection_type, debug
        )
        body = "\n" + "\n" + one_to_many_body + "\n" + field_body + "\n"
        if debug:
            self.logging.log(body, "debug")
        return body

    def generate_many_to_one_template(
        self,
        inverse_side_field_type: str,
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
        many_to_one_body = self.generate_many_to_one_annotation_body(
            fetch_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            nullable,
            debug,
        )
        join_column_body = self.generate_join_column_body(
            inverse_side_field_type, nullable, unique, debug
        )
        field_body = self.generate_field_body(
            inverse_side_field_type, False, None, debug
        )
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
        owning_side_buffer_bytes: bytes,
        owning_side_buffer_path: Path,
        field_type: str,
        owning_side_cascade_persist: bool,
        owning_side_cascade_merge: bool,
        owning_side_cascade_remove: bool,
        owning_side_cascade_refresh: bool,
        owning_side_cascade_detach: bool,
        fetch_type: str,
        mapping_type: str,
        nullable: bool,
        unique: bool,
        collection_type: str,
        orphan_removal: bool,
        inverse_side_cascade_persist: bool,
        inverse_side_cascade_merge: bool,
        inverse_side_cascade_remove: bool,
        inverse_side_cascade_refresh: bool,
        inverse_side_cascade_detach: bool,
        debug: bool = False,
    ):
        related_entities: Dict[str, Tuple[str, Path]] = (
            self.get_bidirectional_buffer_data(
                owning_side_buffer_path, field_type, debug
            )
        )
        owning_side_field_template = self.generate_many_to_one_template(
            related_entities["inverse_side"][0],
            fetch_type,
            owning_side_cascade_persist,
            owning_side_cascade_merge,
            owning_side_cascade_remove,
            owning_side_cascade_refresh,
            owning_side_cascade_detach,
            nullable,
            unique,
            debug,
        )
        owning_side_field_insert_point = (
            self.treesitter_lib.get_entity_field_insert_point(
                owning_side_buffer_bytes, debug
            )
        )
        owning_side_field_bytes = self.treesitter_lib.insert_code_into_position(
            owning_side_field_template,
            owning_side_field_insert_point,
            owning_side_buffer_bytes,
            debug,
        )
        self.treesitter_lib.update_buffer(
            owning_side_field_bytes, owning_side_buffer_path, False, True, True, debug
        )
        if mapping_type == "bidirectional_joincolumn":
            inverse_side_buffer_bytes = self.treesitter_lib.get_bytes_from_path(
                related_entities["inverse_side"][1], debug
            )
            inverse_side_field_template = self.generate_one_to_many_template(
                related_entities["owning_side"][0],
                related_entities["inverse_side"][0],
                inverse_side_cascade_persist,
                inverse_side_cascade_merge,
                inverse_side_cascade_remove,
                inverse_side_cascade_refresh,
                inverse_side_cascade_detach,
                orphan_removal,
                collection_type,
                debug,
            )
            inverse_side_field_insert_point = (
                self.treesitter_lib.get_entity_field_insert_point(
                    inverse_side_buffer_bytes, debug
                )
            )
            one_side_field_bytes = self.treesitter_lib.insert_code_into_position(
                inverse_side_field_template,
                inverse_side_field_insert_point,
                inverse_side_buffer_bytes,
                debug,
            )
            self.treesitter_lib.update_buffer(
                one_side_field_bytes,
                related_entities["inverse_side"][1],
                False,
                True,
                True,
                debug,
            )
