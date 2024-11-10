from pathlib import Path
from typing import List, Optional, Tuple

from tree_sitter import Tree

from custom_types.log_level import LogLevel
from custom_types.java_file_data import JavaFileData
from custom_types.collection_type import CollectionType
from custom_types.fetch_type import FetchType
from custom_types.mapping_type import MappingType
from custom_types.cascade_type import CascadeType
from custom_types.other import Other
from utils.path_utils import PathUtils
from utils.treesitter_utils import TreesitterUtils
from pynvim.api.nvim import Nvim
from utils.common_utils import CommonUtils
from utils.logging import Logging


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

    def process_cascades_params(
        self,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        debug: bool = False,
    ) -> Optional[str]:
        imports_to_add: List[str] = ["jakarta.persistence.CascadeType"]
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
        if debug:
            self.logging.log(
                [
                    f"Cascades: {', '.join(cascades)}",
                    f"Merged cascade params: {merged_params}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
        imports_to_add: List[str] = []
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
            imports_to_add.append("jakarta.persistence.FetchType")
        joined_params = ", ".join(params)
        if debug:
            self.logging.log(
                [
                    f"Joined params: {joined_params}",
                    f"Params body: {joined_params}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
                LogLevel.DEBUG,
            )
        return (collection_name, collection_initialization)

    def get_entity_data_by_class_name(
        self,
        class_name: str,
        debug: bool = False,
    ) -> JavaFileData:
        all_java_files = self.common_utils.get_all_java_files_data(debug)
        all_entities = [f for f in all_java_files if f.is_jpa_entity]
        return [f for f in all_entities if f.file_name == class_name][0]

    def get_entity_data_by_path(
        self,
        file_path: Path,
        debug: bool = False,
    ) -> JavaFileData:
        all_java_files = self.common_utils.get_all_java_files_data(debug)
        all_entities = [f for f in all_java_files if f.is_jpa_entity]
        return [f for f in all_entities if f.path == file_path][0]

    def generate_equals_hashcode_methods(
        self, field_type: str, file_tree: Tree, debug: bool = False
    ) -> Optional[str]:
        imports_to_add: List[str] = [
            "org.hibernate.proxy.HibernateProxy",
            "java.util.Objects",
        ]
        buffer_has_equals_method = self.treesitter_utils.buffer_public_class_has_method(
            file_tree, "equals", debug
        )
        buffer_has_hashcode_method = (
            self.treesitter_utils.buffer_public_class_has_method(
                file_tree, "hashCode", debug
            )
        )
        snaked_field_name = self.common_utils.convert_to_snake_case(field_type, debug)
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
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
        imports_to_add: List[str] = ["jakarta.persistence.OneToMany"]
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
            mapped_by=self.common_utils.convert_to_snake_case(one_field_type),
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
                    f"Orphan removal: {orphan_removal}",
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_many_to_one_annotation_body(
        self,
        fetch_type: FetchType,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        optional: bool,
        debug: bool = False,
    ):
        imports_to_add: List[str] = ["jakarta.persistence.ManyToOne"]
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
            fetch=fetch_type.value if fetch_type != FetchType.NONE else None,
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
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
        imports_to_add: List[str] = ["jakarta.persistence.ManyToMany"]
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
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
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
        imports_to_add: List[str] = ["jakarta.persistence.OneToOne"]
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
                self.common_utils.convert_to_snake_case(inverse_field_type)
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
        if debug:
            self.logging.log(
                [
                    f"Params: {', '.join(params)}",
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_join_table_body(
        self,
        owning_side_field_type: str,
        inverse_side_field_type: str,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = [
            "jakarta.persistence.JoinColumn",
            "jakarta.persistence.JoinTable",
        ]
        snaked_owning_side_field_name = self.common_utils.convert_to_snake_case(
            owning_side_field_type, debug
        )
        snaked_inverse_side_field_name = self.common_utils.convert_to_snake_case(
            inverse_side_field_type, debug
        )
        body = (
            "@JoinTable("
            + f'name = "{snaked_owning_side_field_name}_{snaked_inverse_side_field_name}", '
            + f'joinColumns = @JoinColumn(name = "{snaked_owning_side_field_name}_id"), '
            + f'inverseJoinColumns = @JoinColumn(name = "{snaked_inverse_side_field_name}_id")'
            + ")"
        )
        if debug:
            self.logging.log(
                [
                    f"Snaked owning field name: {owning_side_field_type}",
                    f"Snaked inverse field name: {inverse_side_field_type}",
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_join_column_body(
        self,
        inverse_side_field_type: str,
        nullable: bool,
        unique: bool,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = [
            "jakarta.persistence.JoinColumn",
        ]
        body = "@JoinColumn"
        snaked_field_name = (
            self.common_utils.convert_to_snake_case(inverse_side_field_type, debug)
            + "_id"
        )
        extra_params = self.process_extra_params(
            name=snaked_field_name, nullable=nullable, unique=unique, debug=debug
        )
        body += "(" + extra_params + ")"
        if debug:
            self.logging.log(
                [
                    f"Snaked field name: {inverse_side_field_type}",
                    f"Body: {body}",
                ],
                LogLevel.DEBUG,
            )
            self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_field_body(
        self,
        field_type: str,
        is_collection: bool,
        collection_type: Optional[str],
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = []
        collection_name: str = ""
        if is_collection and collection_type:
            collection_name = collection_type.title()
        field_name = self.common_utils.generate_field_name(
            field_type, True if is_collection else False, debug
        )
        if collection_type == "set":
            imports_to_add.extend(["java.util.Set", "java.util.HashSet"])
        if collection_type == "List":
            imports_to_add.extend(["java.util.List", "java.util.ArrayList"])
        if collection_type == "Collection":
            imports_to_add.extend(["java.util.Collection", "java.util.ArrayList"])
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
                LogLevel.DEBUG,
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_one_to_many_template(
        self,
        owning_side_file_data: JavaFileData,
        inverse_side_file_data: JavaFileData,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        orphan_removal: bool,
        collection_type: CollectionType,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = [
            owning_side_file_data.package_path + "." + owning_side_file_data.file_name
        ]
        one_to_many_body = self.generate_one_to_many_annotation_body(
            inverse_side_file_data.file_name,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            orphan_removal,
            debug,
        )
        field_body = self.generate_field_body(
            owning_side_file_data.file_name, True, collection_type.value, debug
        )
        body = "\n\t" + one_to_many_body + "\n\t" + field_body + "\n"
        if debug:
            self.logging.log(f"Body:\n{body}", LogLevel.DEBUG)
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return body

    def generate_many_to_one_template(
        self,
        inverse_side_file_data: JavaFileData,
        fetch_type: FetchType,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_remove: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        mandatory: bool,
        unique: bool,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = [
            inverse_side_file_data.package_path + "." + inverse_side_file_data.file_name
        ]
        many_to_one_body = self.generate_many_to_one_annotation_body(
            fetch_type,
            cascade_persist,
            cascade_merge,
            cascade_remove,
            cascade_refresh,
            cascade_detach,
            mandatory,
            debug,
        )
        join_column_body = self.generate_join_column_body(
            inverse_side_file_data.file_name, mandatory, unique, debug
        )
        field_body = self.generate_field_body(
            inverse_side_file_data.file_name, False, None, debug
        )
        complete_field_body = (
            "\n\t"
            + many_to_one_body
            + "\n\t"
            + join_column_body
            + "\n\t"
            + field_body
            + "\n"
        )
        if debug:
            self.logging.log(
                f"Complete field body: {complete_field_body}", LogLevel.DEBUG
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return complete_field_body

    def generate_one_to_one_field_template(
        self,
        inverse_side_file_data: JavaFileData,
        owning_side_file_data: Optional[JavaFileData],
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
        imports_to_add: List[str] = [
            inverse_side_file_data.package_path + "." + inverse_side_file_data.file_name
        ]
        one_to_one_body = self.generate_one_to_one_annotation_body(
            cascade_persist=cascade_persist,
            cascade_merge=cascade_merge,
            cascade_remove=cascade_remove,
            cascade_refresh=cascade_refresh,
            cascade_detach=cascade_detach,
            orphan_removal=orphan_removal,
            optional=mandatory,
            inverse_field_type=(
                inverse_side_file_data.file_name
                if owning_side_file_data is not None
                else None
            ),
            debug=debug,
        )
        join_column_body: str = ""
        field_body: str = ""
        if owning_side_file_data is None:
            join_column_body = self.generate_join_column_body(
                inverse_side_file_data.file_name, mandatory, unique, debug
            )
        if owning_side_file_data is not None:
            imports_to_add.append(
                owning_side_file_data.package_path
                + "."
                + owning_side_file_data.file_name
            )
            field_body = self.generate_field_body(
                owning_side_file_data.file_name, False, None, debug
            )
        else:
            field_body = self.generate_field_body(
                inverse_side_file_data.file_name, False, None, debug
            )
        complete_field_body = "\n\t" + one_to_one_body
        if owning_side_file_data is None:
            complete_field_body += "\n\t" + join_column_body
        complete_field_body += "\n\t" + field_body + "\n"
        if debug:
            self.logging.log(
                f"Complete field body: {complete_field_body}", LogLevel.DEBUG
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return complete_field_body

    def generate_many_to_many_field_template(
        self,
        owning_side_file_data: JavaFileData,
        inverse_side_file_data: JavaFileData,
        cascade_persist: bool,
        cascade_merge: bool,
        cascade_refresh: bool,
        cascade_detach: bool,
        equals_hashcode: bool,
        owning_side: bool,
        debug: bool = False,
    ) -> str:
        imports_to_add: List[str] = [
            inverse_side_file_data.package_path + "." + inverse_side_file_data.file_name
        ]
        many_to_many_body = self.generate_many_to_many_annotation_body(
            cascade_persist,
            cascade_merge,
            cascade_refresh,
            cascade_detach,
            inverse_side_file_data.file_name if owning_side else None,
            debug,
        )
        join_table_body: str = ""
        field_body: str = ""
        if owning_side:
            join_table_body = self.generate_join_table_body(
                owning_side_file_data.file_name, inverse_side_file_data.file_name, debug
            )
            field_body = self.generate_field_body(
                inverse_side_file_data.file_name, True, "set"
            )
        else:
            field_body = self.generate_field_body(
                owning_side_file_data.file_name, True, "set", debug
            )
            imports_to_add.append(
                owning_side_file_data.package_path
                + "."
                + owning_side_file_data.file_name
            )
        complete_field_body = "\n\t" + many_to_many_body
        if owning_side:
            complete_field_body += "\n\t" + join_table_body
        complete_field_body += "\n\t" + field_body + "\n"
        if not owning_side and equals_hashcode:
            equals_and_hashcode = self.generate_equals_hashcode_methods(
                inverse_side_file_data.file_name, inverse_side_file_data.tree, debug
            )
            if equals_and_hashcode is not None:
                complete_field_body += equals_and_hashcode
        if debug:
            self.logging.log(
                f"Complete field body: {complete_field_body}", LogLevel.DEBUG
            )
        self.treesitter_utils.add_to_importing_list(imports_to_add, debug)
        return complete_field_body

    def update_buffer(
        self, buffer_tree: Tree, buffer_path: Path, template: str, debug: bool = False
    ) -> None:
        updated_buffer_tree = self.treesitter_utils.add_imports_to_file_tree(
            buffer_tree, debug
        )
        insert_byte = self.treesitter_utils.get_entity_field_insert_byte(
            updated_buffer_tree, debug
        )
        if not insert_byte:
            error_msg = "Unable to get field insert position"
            self.logging.log(error_msg, LogLevel.ERROR)
            raise ValueError(error_msg)
        updated_buffer_tree = self.treesitter_utils.insert_code_at_position(
            template, insert_byte, updated_buffer_tree
        )
        self.treesitter_utils.update_buffer(
            tree=updated_buffer_tree, buffer_path=buffer_path, save=True, debug=debug
        )
        if debug:
            self.logging.log(
                [
                    f"Template:\n{template}\n"
                    f"Node before:\n{self.treesitter_utils.get_node_text_as_string(buffer_tree.root_node)}\n"
                    f"Node after:\n{self.treesitter_utils.get_node_text_as_string(updated_buffer_tree.root_node)}\n"
                ],
                LogLevel.DEBUG,
            )

    def create_many_to_one_relationship_field(
        self,
        owning_side_file_data: JavaFileData,
        inverse_side_file_data: JavaFileData,
        collection_type: CollectionType,
        fetch_type: FetchType,
        mapping_type: MappingType,
        owning_side_cascades: List[CascadeType],
        inverse_side_cascades: List[CascadeType],
        inverse_side_other: List[Other],
        owning_side_other: List[Other],
        debug: bool = False,
    ):
        field_template = self.generate_many_to_one_template(
            inverse_side_file_data=inverse_side_file_data,
            fetch_type=fetch_type,
            cascade_persist=True
            if CascadeType.PERSIST in owning_side_cascades
            else False,
            cascade_merge=True if CascadeType.MERGE in owning_side_cascades else False,
            cascade_remove=True
            if CascadeType.REMOVE in owning_side_cascades
            else False,
            cascade_refresh=True
            if CascadeType.REFRESH in owning_side_cascades
            else False,
            cascade_detach=True
            if CascadeType.DETACH in owning_side_cascades
            else False,
            mandatory=True if Other.MANDATORY in owning_side_other else False,
            unique=True if Other.UNIQUE in owning_side_other else False,
            debug=debug,
        )
        self.update_buffer(
            owning_side_file_data.tree,
            owning_side_file_data.path,
            field_template,
            debug,
        )
        if mapping_type == MappingType.BIDIRECTIONAL_JOIN_COLUMN:
            field_template = self.generate_one_to_many_template(
                owning_side_file_data=owning_side_file_data,
                inverse_side_file_data=inverse_side_file_data,
                cascade_persist=True
                if CascadeType.PERSIST in inverse_side_cascades
                else False,
                cascade_merge=True
                if CascadeType.MERGE in inverse_side_cascades
                else False,
                cascade_remove=True
                if CascadeType.REMOVE in inverse_side_cascades
                else False,
                cascade_refresh=True
                if CascadeType.REFRESH in inverse_side_cascades
                else False,
                cascade_detach=True
                if CascadeType.DETACH in inverse_side_cascades
                else False,
                orphan_removal=True
                if Other.ORPHAN_REMOVAL in inverse_side_other
                else False,
                collection_type=collection_type,
            )
            self.update_buffer(
                inverse_side_file_data.tree,
                inverse_side_file_data.path,
                field_template,
                debug,
            )

    def create_one_to_one_relationship_field(
        self,
        owning_side_file_data: JavaFileData,
        inverse_side_file_data: JavaFileData,
        mapping_type: MappingType,
        owning_side_cascades: List[CascadeType],
        inverse_side_cascades: List[CascadeType],
        inverse_side_other: List[Other],
        owning_side_other: List[Other],
        debug: bool = False,
    ):
        field_template = self.generate_one_to_one_field_template(
            inverse_side_file_data=inverse_side_file_data,
            owning_side_file_data=None,
            cascade_persist=True
            if CascadeType.PERSIST in owning_side_cascades
            else False,
            cascade_merge=True if CascadeType.MERGE in owning_side_cascades else False,
            cascade_remove=True
            if CascadeType.REMOVE in owning_side_cascades
            else False,
            cascade_refresh=True
            if CascadeType.REFRESH in owning_side_cascades
            else False,
            cascade_detach=True
            if CascadeType.DETACH in owning_side_cascades
            else False,
            mandatory=True if Other.MANDATORY in owning_side_other else False,
            unique=True if Other.UNIQUE in owning_side_other else False,
            orphan_removal=True if Other.ORPHAN_REMOVAL in owning_side_other else False,
            debug=debug,
        )
        self.update_buffer(
            owning_side_file_data.tree,
            owning_side_file_data.path,
            field_template,
            debug,
        )
        if mapping_type != MappingType.UNIDIRECTIONAL_JOIN_COLUMN:
            field_template = self.generate_one_to_one_field_template(
                inverse_side_file_data=inverse_side_file_data,
                owning_side_file_data=owning_side_file_data,
                cascade_persist=True
                if CascadeType.PERSIST in inverse_side_cascades
                else False,
                cascade_merge=True
                if CascadeType.MERGE in inverse_side_cascades
                else False,
                cascade_remove=True
                if CascadeType.REMOVE in inverse_side_cascades
                else False,
                cascade_refresh=True
                if CascadeType.REFRESH in inverse_side_cascades
                else False,
                cascade_detach=True
                if CascadeType.DETACH in inverse_side_cascades
                else False,
                mandatory=True if Other.MANDATORY in inverse_side_other else False,
                unique=True if Other.UNIQUE in owning_side_other else False,
                orphan_removal=True
                if Other.ORPHAN_REMOVAL in inverse_side_other
                else False,
                debug=debug,
            )
            self.update_buffer(
                inverse_side_file_data.tree,
                inverse_side_file_data.path,
                field_template,
                debug,
            )

    def create_many_to_many_relationship_field(
        self,
        owning_side_file_data: JavaFileData,
        inverse_side_file_data: JavaFileData,
        mapping_type: MappingType,
        owning_side_cascades: List[CascadeType],
        inverse_side_cascades: List[CascadeType],
        inverse_side_other: List[Other],
        debug: bool = False,
    ):
        field_template = self.generate_many_to_many_field_template(
            owning_side_file_data=owning_side_file_data,
            inverse_side_file_data=inverse_side_file_data,
            cascade_persist=True
            if CascadeType.PERSIST in owning_side_cascades
            else False,
            cascade_merge=True if CascadeType.MERGE in owning_side_cascades else False,
            cascade_refresh=True
            if CascadeType.REFRESH in owning_side_cascades
            else False,
            cascade_detach=True
            if CascadeType.DETACH in owning_side_cascades
            else False,
            equals_hashcode=False,
            owning_side=True,
            debug=debug,
        )
        self.update_buffer(
            owning_side_file_data.tree,
            owning_side_file_data.path,
            field_template,
            debug,
        )
        if mapping_type != MappingType.UNIDIRECTIONAL_JOIN_COLUMN:
            field_template = self.generate_many_to_many_field_template(
                owning_side_file_data=owning_side_file_data,
                inverse_side_file_data=inverse_side_file_data,
                cascade_persist=True
                if CascadeType.PERSIST in inverse_side_cascades
                else False,
                cascade_merge=True
                if CascadeType.MERGE in inverse_side_cascades
                else False,
                cascade_refresh=True
                if CascadeType.REFRESH in inverse_side_cascades
                else False,
                cascade_detach=True
                if CascadeType.DETACH in inverse_side_cascades
                else False,
                equals_hashcode=True
                if Other.EQUALS_HASHCODE in inverse_side_other
                else False,
                owning_side=False,
                debug=debug,
            )
            self.update_buffer(
                inverse_side_file_data.tree,
                inverse_side_file_data.path,
                field_template,
                debug,
            )
