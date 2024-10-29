from pathlib import Path
from re import sub
from typing import List, Optional, Tuple

from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils
from pynvim.api.nvim import Nvim
from utils.common_utils import CommonUtils
from utils.logging import Logging
from utils.data_types import (
    CollectionType,
    FetchType,
    MappingType,
    CascadeType,
    SelectedOther,
)


class EntityRelationshipUtils:
    def __init__(
        self,
        nvim: Nvim,
        treesitter_utils: TreesitterUtils,
        path_utils: PathUtils,
        common_utils: CommonUtils,
        logging: Logging,
    ):
        self.nvim = nvim
        self.treesitter_utils = treesitter_utils
        self.path_utils = path_utils
        self.common_utils = common_utils
        self.logging = logging
        self.importings: List[str] = []

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
        merged_params: Optional[str]
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
            merged_params = "cascade = CascadeType.ALL"
        elif len(cascades) == 1:
            merged_params = f"cascade = CascadeType.{cascades[0]}"
        elif len(cascades) == 0:
            merged_params = None
        else:
            merged_params = (
                f"cascade = {{{', '.join([f'CascadeType.{c}' for c in cascades])}}}"
            )
        if "jakarta.persistence.CascadeType" not in self.importings:
            self.importings.append("jakarta.persistence.CascadeType")
        if debug:
            self.logging.log(
                [
                    f"Cascades: {', '.join(cascades)}",
                    f"Merged cascade params: {merged_params}",
                ],
                "debug",
            )
        return merged_params

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
            params.append(f'mappedBy = "{mapped_by.lower()}"')
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
            if "jakarta.persistence.FetchType" not in self.importings:
                self.importings.append("jakarta.persistence.FetchType")
        joined_params = ", ".join(params)
        if debug:
            self.logging.log(
                [
                    f"Joined params: {joined_params}",
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
                    f"Collection name: {collection_name}",
                    f"Collection initialization: {collection_initialization}",
                ],
                "debug",
            )
        return (collection_name, collection_initialization)

    def get_entity_data_by_class_name(
        self,
        class_name: str,
        debug: bool = False,
    ) -> Tuple[str, str, Path]:
        all_entities = self.path_utils.get_all_jpa_entities(debug)
        found_entity: Optional[Tuple[str, str, Path]] = None
        for k, v in all_entities.items():
            if k == class_name:
                found_entity = (k, v[0], v[1])
        if debug:
            self.logging.log(f"Buffer data: {str(found_entity)}", "debug")
        if not found_entity:
            error_msg = f"No entity called {class_name} was found"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        return found_entity

    def get_entity_data_by_path(
        self,
        buffer_path: Path,
        debug: bool = False,
    ) -> Tuple[str, str, Path]:
        all_entities = self.path_utils.get_all_jpa_entities(debug)
        found_entity: Optional[Tuple[str, str, Path]] = None
        for k, v in all_entities.items():
            if v[1] == buffer_path:
                found_entity = (k, v[0], v[1])
        if debug:
            self.logging.log(f"Buffer data: {str(found_entity)}", "debug")
        if not found_entity:
            error_msg = f"No entity with path {str(buffer_path)} was found"
            self.logging.log(error_msg, "error")
            raise FileNotFoundError(error_msg)
        return found_entity

    def generated_snaked_field_name(self, field_type: str, debug: bool = False) -> str:
        snaked_field_name = sub(r"(?<!^)(?=[A-Z])", "_", field_type).lower()
        if debug:
            self.logging.log(
                f"Snaked field name: {snaked_field_name}",
                "debug",
            )
        return snaked_field_name

    def generate_equals_hashcode_methods(
        self, field_type: str, buffer_path: Path, debug: bool = False
    ) -> Optional[str]:
        buffer_has_equals_method = self.treesitter_utils.buffer_has_method(
            buffer_path, "equals", debug
        )
        buffer_has_hashcode_method = self.treesitter_utils.buffer_has_method(
            buffer_path, "hashCode", debug
        )
        snaked_field_name = self.generated_snaked_field_name(field_type, debug)
        equals_method = f"""
        @Override
        public final boolean equals(Object o) {{
            if (this == o) return true;
            if (o == null) return false;
            Class<?> oEffectiveClass =
                    o instanceof HibernateProxy
                            ? ((HibernateProxy) o).getHibernateLazyInitializer().getPersistentClass()
                            : o.getClass();
            Class<?> thisEffectiveClass =
                    this instanceof HibernateProxy
                            ? ((HibernateProxy) this).getHibernateLazyInitializer().getPersistentClass()
                            : this.getClass();
            if (thisEffectiveClass != oEffectiveClass) return false;
            {field_type} {snaked_field_name} = ({field_type}) o;
            return getId() != null && Objects.equals(getId(), {snaked_field_name}.getId());
        }}
        """
        hashcode_method = """
        @Override
        public final int hashCode() {
            return this instanceof HibernateProxy
                    ? ((HibernateProxy) this)
                            .getHibernateLazyInitializer()
                            .getPersistentClass()
                            .hashCode()
                    : getClass().hashCode();
        }
        """
        if debug:
            self.logging.log(
                [
                    f"Buffer has equals method: {buffer_has_equals_method}",
                    f"Buffer has hashCode method: {buffer_has_hashcode_method}",
                    f"Snaked field name: {snaked_field_name}",
                    f"Equals method: {equals_method}",
                    f"HashCode method: {hashcode_method}",
                    f"Equals and hashCode added: {str(not buffer_has_hashcode_method and buffer_has_equals_method)}",
                ],
                "debug",
            )
        if not buffer_has_equals_method and not buffer_has_hashcode_method:
            return equals_method + "\n" + hashcode_method
        return None

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
            orphan_removal=orphan_removal,
            mapped_by=self.generated_snaked_field_name(one_field_type),
            debug=debug,
        )
        params.append(extra_params)
        if cascade_param:
            params.append(cascade_param)
        if len(params) > 0:
            body += "(" + ", ".join(params) + ")"
        if "jakarta.persistence.OneToMany" not in self.importings:
            self.importings.append("jakarta.persistence.OneToMany")
        if debug:
            self.logging.log(
                [
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
        if "jakarta.persistence.ManyToOne" not in self.importings:
            self.importings.append("jakarta.persistence.ManyToOne")
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_many_to_many_annotation_body(
        self,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        mapped_by: Optional[str] = None,
        debug: bool = False,
    ):
        body = "@ManyToMany"
        params: List[str] = []
        extra_params: Optional[str]
        cascade_param: Optional[str] = self.process_cascades_params(
            cascade_persist,
            cascade_merge,
            False,
            cascade_refresh,
            cascade_detach,
            debug,
        )
        if mapped_by is not None:
            extra_params = self.process_extra_params(
                mapped_by=mapped_by if mapped_by is not None else None,
                debug=debug,
            )
            params.append(extra_params)
        if cascade_param:
            params.append(cascade_param)
        if len(params) > 0:
            body += "(" + ", ".join(params) + ")"
        if "jakarta.persistence.ManyToMany" not in self.importings:
            self.importings.append("jakarta.persistence.ManyToMany")
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_one_to_one_annotation_body(
        self,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        optional: bool,
        inverse_field_type: Optional[str],
        debug: bool = False,
    ):
        body = "@OneToOne"
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
            mapped_by=(
                self.generated_snaked_field_name(inverse_field_type)
                if inverse_field_type is not None
                else None
            ),
            optional=optional,
            orphan_removal=orphan_removal,
            debug=debug,
        )
        params.append(extra_params)
        if cascade_param:
            params.append(cascade_param)
        if len(params) > 0:
            body += "(" + ", ".join(params) + ")"
        if "jakarta.persistence.OneToOne" not in self.importings:
            self.importings.append("jakarta.persistence.OneToOne")
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Body: {body}",
                ],
                "debug",
            )
        return body

    def generate_join_table_body(
        self,
        owning_side_field_type: str,
        inverse_side_field_type: str,
        debug: bool = False,
    ) -> str:
        snaked_owning_side_field_name = self.generated_snaked_field_name(
            owning_side_field_type, debug
        )
        snaked_inverse_side_field_name = self.generated_snaked_field_name(
            inverse_side_field_type, debug
        )
        body = (
            "@JoinTable("
            + f'name = "{snaked_owning_side_field_name}_{snaked_inverse_side_field_name}", '
            + f'joinColumns = @JoinColumn(name = "{snaked_owning_side_field_name}_id"), '
            + f'inverseJoinColumns = @JoinColumn(name = "{snaked_inverse_side_field_name}_id")'
            + ")"
        )
        if "jakarta.persistence.JoinColumn" not in self.importings:
            self.importings.append("jakarta.persistence.JoinColumn")
        if "jakarta.persistence.JoinTable" not in self.importings:
            self.importings.append("jakarta.persistence.JoinTable")
        if debug:
            self.logging.log(
                [
                    f"Snaked owning field name: {owning_side_field_type}",
                    f"Snaked inverse field name: {inverse_side_field_type}",
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
        snaked_field_name = (
            self.generated_snaked_field_name(inverse_side_field_type, debug) + "_id"
        )
        extra_params = self.process_extra_params(
            name=snaked_field_name, nullable=nullable, unique=unique, debug=debug
        )
        body += "(" + extra_params + ")"
        if "jakarta.persistence.JoinColumn" not in self.importings:
            self.importings.append("jakarta.persistence.JoinColumn")
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {inverse_side_field_type}",
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
        field_name = self.common_utils.generate_field_name(
            field_type, True if is_collection else False, debug
        )
        if collection_type == "set":
            if "java.util.Set" not in self.importings:
                self.importings.append("java.util.Set")
            if "java.util.HashSet" not in self.importings:
                self.importings.append("java.util.HashSet")
        if collection_type == "List":
            if "java.util.List" not in self.importings:
                self.importings.append("java.util.List")
            if "java.util.ArrayList" not in self.importings:
                self.importings.append("java.util.ArrayList")
        if collection_type == "Collection":
            if "java.util.Collection" not in self.importings:
                self.importings.append("java.util.Collection")
            if "java.util.ArrayList" not in self.importings:
                self.importings.append("java.util.ArrayList")
        body = (
            f"private {collection_name}"
            f"{'<' if is_collection else ''}{field_type}{'>' if is_collection else ''} "
            f"{field_name};"
        )
        if debug:
            self.logging.log(
                [
                    f"Field name: {field_name}",
                    f"Field body: {body}",
                ],
                "debug",
            )
        return body

    def generate_one_to_many_template(
        self,
        owning_side_package_path: str,
        owning_side_field_type: str,
        inverse_field_type: str,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        collection_type: str,
        debug: bool = False,
    ) -> str:
        self.importings.append(owning_side_package_path + "." + owning_side_field_type)
        one_to_many_body = self.generate_one_to_many_annotation_body(
            inverse_field_type,
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
            self.logging.log(f"Body:\n{body}", "debug")
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
            self.logging.log(f"Complete field body: {complete_field_body}", "debug")
        return complete_field_body

    def generate_one_to_one_field_template(
        self,
        inverse_side_field_type: str,
        owning_side_field_type: Optional[str],
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        mandatory: bool,
        unique: bool,
        orphan_removal: bool,
        debug: bool = False,
    ) -> str:
        one_to_one_body = self.generate_one_to_one_annotation_body(
            cascade_persist=cascade_persist,
            cascade_merge=cascade_merge,
            cascade_remove=cascade_remove,
            cascade_refresh=cascade_refresh,
            cascade_detach=cascade_detach,
            orphan_removal=orphan_removal,
            optional=mandatory,
            inverse_field_type=(
                inverse_side_field_type if owning_side_field_type is not None else None
            ),
            debug=debug,
        )
        join_column_body: str = ""
        field_body: str = ""
        if owning_side_field_type is None:
            join_column_body = self.generate_join_column_body(
                inverse_side_field_type, mandatory, unique, debug
            )
        if owning_side_field_type is not None:
            field_body = self.generate_field_body(
                owning_side_field_type, False, None, debug
            )
        else:
            field_body = self.generate_field_body(
                inverse_side_field_type, False, None, debug
            )
        complete_field_body = "\n" + "\n" + one_to_one_body
        if owning_side_field_type is None:
            complete_field_body += "\n" + join_column_body
        complete_field_body += "\n" + field_body + "\n"
        if debug:
            self.logging.log(f"Complete field body: {complete_field_body}", "debug")
        return complete_field_body

    def generate_many_to_many_field_template(
        self,
        owning_side_field_type: str,
        owning_side_package_path: str,
        inverse_side_field_type: str,
        inverse_side_field_path: Path,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        equals_hashcode: bool,
        owning_side: bool,
        debug: bool = False,
    ) -> str:
        many_to_many_body = self.generate_many_to_many_annotation_body(
            cascade_persist,
            cascade_merge,
            cascade_refresh,
            cascade_detach,
            inverse_side_field_type if owning_side is False else None,
            debug,
        )
        join_table_body: str = ""
        field_body: str = ""
        if owning_side:
            join_table_body = self.generate_join_table_body(
                owning_side_field_type, inverse_side_field_type, debug
            )
            field_body = self.generate_field_body(inverse_side_field_type, True, "set")
        else:
            field_body = self.generate_field_body(
                owning_side_field_type, True, "set", debug
            )
            self.importings.append(
                owning_side_package_path + "." + owning_side_field_type
            )
        complete_field_body = "\n" + "\n" + many_to_many_body
        if owning_side:
            complete_field_body += "\n" + join_table_body
        complete_field_body += "\n" + field_body + "\n"
        if not owning_side and equals_hashcode:
            equals_and_hashcode = self.generate_equals_hashcode_methods(
                inverse_side_field_type, inverse_side_field_path, debug
            )
            if equals_and_hashcode is not None:
                complete_field_body += equals_and_hashcode
        if debug:
            self.logging.log(f"Complete field body: {complete_field_body}", "debug")
        return complete_field_body

    def create_many_to_one_relationship_field(
        self,
        owning_side_buffer_bytes: bytes,
        owning_side_buffer_path: Path,
        collection_type: CollectionType,
        fetch_type: FetchType,
        mapping_type: MappingType,
        inverse_side_type: str,
        owning_side_cascades: CascadeType,
        inverse_side_cascades: CascadeType,
        inverse_side_other: SelectedOther,
        owning_side_other: SelectedOther,
        debug: bool = False,
    ):
        field_template = self.generate_many_to_one_template(
            inverse_side_type,
            fetch_type,
            True if "persist" in owning_side_cascades else False,
            True if "merge" in owning_side_cascades else False,
            True if "remove" in owning_side_cascades else False,
            True if "refresh" in owning_side_cascades else False,
            True if "detach" in owning_side_cascades else False,
            True if "mandatory" in owning_side_other else False,
            True if "unique" in owning_side_other else False,
            debug,
        )
        field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
            owning_side_buffer_bytes, debug
        )
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            field_template,
            field_insert_point,
            owning_side_buffer_bytes,
            debug,
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes, owning_side_buffer_path, False, True, True, debug
        )
        if mapping_type == "bidirectional_join_column":
            owning_side_field_data = self.get_entity_data_by_path(
                owning_side_buffer_path, debug
            )
            inverse_side_field_data = self.get_entity_data_by_class_name(
                inverse_side_type, debug
            )
            inverse_side_buffer_bytes = self.treesitter_utils.get_bytes_from_path(
                inverse_side_field_data[2]
            )
            field_template = self.generate_one_to_many_template(
                owning_side_field_data[1],
                owning_side_field_data[0],
                inverse_side_type,
                True if "persist" in inverse_side_cascades else False,
                True if "merge" in inverse_side_cascades else False,
                True if "remove" in inverse_side_cascades else False,
                True if "refresh" in inverse_side_cascades else False,
                True if "detach" in inverse_side_cascades else False,
                True if "orphan_removal" in inverse_side_other else False,
                collection_type,
            )
            field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
                inverse_side_buffer_bytes, debug
            )
            buffer_bytes = self.treesitter_utils.insert_code_into_position(
                field_template, field_insert_point, inverse_side_buffer_bytes, debug
            )
            buffer_bytes = self.common_utils.add_imports_to_buffer(
                self.importings, buffer_bytes, debug
            )
            self.treesitter_utils.update_buffer(
                buffer_bytes, inverse_side_field_data[2], False, True, True, debug
            )
            if debug:
                self.logging.log(
                    f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n",
                    "debug",
                )

    def create_one_to_one_relationship_field(
        self,
        owning_side_buffer_path: Path,
        inverse_side_type: str,
        mapping_type: MappingType,
        owning_side_cascades: CascadeType,
        inverse_side_cascades: CascadeType,
        inverse_side_other: SelectedOther,
        owning_side_other: SelectedOther,
        debug: bool = False,
    ):
        owning_side_field_data = self.get_entity_data_by_path(
            owning_side_buffer_path, debug
        )
        inverse_side_field_data = self.get_entity_data_by_class_name(
            inverse_side_type, debug
        )
        field_template = self.generate_one_to_one_field_template(
            inverse_side_field_data[0],
            None,
            True if "persist" in owning_side_cascades else False,
            True if "merge" in owning_side_cascades else False,
            True if "remove" in owning_side_cascades else False,
            True if "refresh" in owning_side_cascades else False,
            True if "detach" in owning_side_cascades else False,
            True if "mandatory" in owning_side_other else False,
            True if "unique" in owning_side_other else False,
            True if "orphan_removal" in owning_side_other else False,
            debug,
        )
        buffer_bytes = self.treesitter_utils.get_bytes_from_path(
            owning_side_field_data[2],
            debug,
        )
        field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            field_template,
            field_insert_point,
            buffer_bytes,
            debug,
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes,
            owning_side_field_data[2],
            False,
            True,
            True,
            debug,
        )
        if mapping_type != "unidirectional_join_column":
            field_template = self.generate_one_to_one_field_template(
                inverse_side_field_data[0],
                owning_side_field_data[0],
                True if "persist" in inverse_side_cascades else False,
                True if "merge" in inverse_side_cascades else False,
                True if "remove" in inverse_side_cascades else False,
                True if "refresh" in inverse_side_cascades else False,
                True if "detach" in inverse_side_cascades else False,
                True if "mandatory" in inverse_side_other else False,
                True if "orphan_removal" in inverse_side_other else False,
                debug,
            )
            buffer_bytes = self.treesitter_utils.get_bytes_from_path(
                inverse_side_field_data[2],
                debug,
            )
            field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
                buffer_bytes, debug
            )
            buffer_bytes = self.treesitter_utils.insert_code_into_position(
                field_template,
                field_insert_point,
                buffer_bytes,
                debug,
            )
            self.treesitter_utils.update_buffer(
                buffer_bytes,
                inverse_side_field_data[2],
                False,
                True,
                True,
                debug,
            )
        if debug:
            self.logging.log(
                f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n",
                "debug",
            )

    def create_many_to_many_relationship_field(
        self,
        owning_side_buffer_path: Path,
        inverse_side_type: str,
        mapping_type: MappingType,
        owning_side_cascades: CascadeType,
        inverse_side_cascades: CascadeType,
        inverse_side_other: SelectedOther,
        debug: bool = False,
    ):
        pass
        owning_side_field_data = self.get_entity_data_by_path(
            owning_side_buffer_path, debug
        )
        inverse_side_field_data = self.get_entity_data_by_class_name(
            inverse_side_type, debug
        )
        field_template = self.generate_many_to_many_field_template(
            owning_side_field_data[0],
            owning_side_field_data[1],
            inverse_side_field_data[0],
            inverse_side_field_data[2],
            True if "persist" in owning_side_cascades else False,
            True if "merge" in owning_side_cascades else False,
            True if "refresh" in owning_side_cascades else False,
            True if "detach" in owning_side_cascades else False,
            False,
            True,
            debug,
        )
        buffer_bytes = self.treesitter_utils.get_bytes_from_path(
            owning_side_buffer_path,
            debug,
        )
        field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
            buffer_bytes, debug
        )
        buffer_bytes = self.treesitter_utils.insert_code_into_position(
            field_template,
            field_insert_point,
            buffer_bytes,
            debug,
        )
        buffer_bytes = self.common_utils.add_imports_to_buffer(
            self.importings, buffer_bytes, debug
        )
        self.treesitter_utils.update_buffer(
            buffer_bytes,
            owning_side_buffer_path,
            False,
            True,
            True,
            debug,
        )
        if mapping_type != "unidirectional_join_column":
            field_template = self.generate_many_to_many_field_template(
                owning_side_field_data[0],
                owning_side_field_data[1],
                inverse_side_field_data[0],
                inverse_side_field_data[2],
                True if "persist" in inverse_side_cascades else False,
                True if "merge" in inverse_side_cascades else False,
                True if "refresh" in inverse_side_cascades else False,
                True if "detach" in inverse_side_cascades else False,
                True if "equals_hashcode" in inverse_side_other else False,
                False,
                debug,
            )
            buffer_bytes = self.treesitter_utils.get_bytes_from_path(
                inverse_side_field_data[2],
                debug,
            )
            field_insert_point = self.treesitter_utils.get_entity_field_insert_point(
                buffer_bytes, debug
            )
            buffer_bytes = self.treesitter_utils.insert_code_into_position(
                field_template,
                field_insert_point,
                buffer_bytes,
                debug,
            )
            buffer_bytes = self.common_utils.add_imports_to_buffer(
                self.importings, buffer_bytes, debug
            )
            self.treesitter_utils.update_buffer(
                buffer_bytes,
                inverse_side_field_data[2],
                False,
                True,
                True,
                debug,
            )
        if debug:
            self.logging.log(
                f"Buffer after:\n{buffer_bytes.decode('utf-8')}\n",
                "debug",
            )
