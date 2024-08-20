from pathlib import Path
from typing import Dict, List, Literal, Tuple

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
        return entities_found

    def generate_many_to_one_annotation(
        self,
        fetch_type: Literal["none", "lazy", "eager"],
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
    ):
        body = "@ManyToOne"
        fetch_type_param: List[str] = []
        cascade_params: List[str] = []
        cascades: List[str] = []
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
            fetch_type_param.append(f"FetchType.{fetch_type.upper()}")
        if len(cascades) == 5:
            cascade_params.append("CascadeType.ALL")
        else:
            [cascade_params.append(f"CascadeType.{c}") for c in cascades]
        if len(fetch_type_param) > 0 or len(cascade_params) > 0:
            body += "("
            if len(fetch_type_param) == 1:
                body += f"fetch = {fetch_type_param[0]}"
            if len(fetch_type_param) > 1:
                body += f"fetch = {{{", ".join(fetch_type_param)}}}"
            if len(fetch_type_param) >= 1 and len(cascade_params) >= 1:
                body += ", "
            if len(cascade_params) > 1:
                body += f"cascade = {{{', '.join(cascade_params)}}}"
            else:
                if len(cascade_params) == 1:
                    body += f"cascade = {cascade_params[0]}"
            body += ")"
        return body + "\n"

    def create_many_to_one_relationship(
        self,
        buffer_bytes: bytes,
        buffer_path: Path,
        field_type: str,
        field_name: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        mapping_type: str,
        nullable: bool,
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
        test = self.generate_many_to_one_annotation(
            "lazy", True, True, False, False, False
        )
        test1 = self.generate_many_to_one_annotation(
            "none", True, False, False, False, False
        )
        test2 = self.generate_many_to_one_annotation(
            "none", True, True, True, True, True
        )
        self.nvim.command(f"echomsg '{test}'")
        self.nvim.command(f"echomsg '{test1}'")
        self.nvim.command(f"echomsg '{test2}'")
