from pathlib import Path

from pynvim.api.nvim import Nvim
from tree_sitter import Node

from pathutil import PathUtil
from tsutil import TreesitterUtil
from messaging import Messaging


class CreateJpaRepository:
    def __init__(
        self,
        nvim: Nvim,
        tsutil: TreesitterUtil,
        pathutil: PathUtil,
        messaging: Messaging,
    ):
        self.nvim = nvim
        self.tsutil = tsutil
        self.pathutil = pathutil
        self.messaging = messaging
        self.class_annotation_query = """
        (class_declaration
            (modifiers
                (marker_annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        self.field_declaration_query = """
        (field_declaration
            (modifiers
                (annotation
                name: (identifier) @annotation_name
                )
            )
        )
        """
        self.id_field_annotation_query = """
        (modifiers
            (marker_annotation
                name: (identifier) @annotation_name
            )
        )
        """
        self.superclass_query = """
        (superclass
            (type_identifier) @superclass_name
         )
        """
        self.class_name_query = """
        (class_declaration
            name: (identifier) @class_name
            )
        """

    def get_boiler_plate(
        self, class_name: str, package_path: str, id_type: str, debugger: bool = False
    ) -> str:
        boiler_plate = (
            f"package {package_path};\n\n"
            f"import org.springframework.data.jpa.repository.JpaRepository;\n\n"
            f"public interface {class_name}Repository extends JpaRepository<{class_name}, {id_type}> {{}}"
        )
        if debugger:
            self.messaging.log(f"Boiler plate: {boiler_plate}", "debug")
        return boiler_plate

    def is_buffer_jpa_entity(self, buffer_node: Node, debugger: bool = False) -> bool:
        results = self.tsutil.query_node(
            buffer_node, self.class_annotation_query, debugger=debugger
        )
        buffer_is_entity = self.tsutil.query_results_has_term(
            results, "Entity", debugger=debugger
        )
        if not buffer_is_entity:
            return False
        return True

    def buffer_has_id_field(self, buffer_node: Node, debugger: bool = False) -> bool:
        results = self.tsutil.query_node(
            buffer_node, self.id_field_annotation_query, debugger=debugger
        )
        id_annotation_found = self.tsutil.query_results_has_term(
            results, "Id", debugger=debugger
        )
        if not id_annotation_found:
            return False
        return True

    def get_buffer_superclass_node(
        self, buffer_node: Node, debugger: bool = False
    ) -> Node | None:
        results = self.tsutil.query_node(
            buffer_node, self.superclass_query, debugger=debugger
        )
        if len(results) == 0:
            return None
        return results[0][0]

    def find_superclass_buffer(
        self, root_path: Path, superclass_name: str, debugger: bool = False
    ) -> Node | None:
        for p in root_path.rglob("*.java"):
            _node = self.tsutil.get_node_from_path(p, debugger=debugger)
            _results = self.tsutil.query_node(
                _node, self.class_name_query, debugger=debugger
            )
            if len(_results) == 0:
                continue
            class_name = self.tsutil.get_node_text(_results[0][0], debugger=debugger)
            if class_name == superclass_name:
                return _node
        return None

    def find_id_field_type_identifier(
        self, buffer_node: Node, debugger: bool = False
    ) -> str | None:
        marker_annotation_name = "Id"
        id_annotation_found = False
        if buffer_node.type == "field_declaration":
            for c1 in buffer_node.children:
                if not id_annotation_found and c1.type == "modifiers":
                    for c2 in c1.children:
                        if c2.type == "marker_annotation":
                            for c3 in c2.children:
                                if c3.type == "identifier":
                                    if (
                                        self.tsutil.get_node_text(c3)
                                        == marker_annotation_name
                                    ):
                                        id_annotation_found = True
                                        if debugger:
                                            self.messaging.log(
                                                f"Id annotation found: {self.tsutil.get_node_text(c3)}",
                                                "debug",
                                            )
                if id_annotation_found:
                    if c1.type == "type_identifier":
                        id_type = self.tsutil.get_node_text(c1)
                        if debugger:
                            self.messaging.log(f"Id type found: {id_type}", "debug")
                        return id_type
        for child in buffer_node.children:
            result = self.find_id_field_type_identifier(child)
            if result:
                return result
        self.messaging.log(
            "Could not locate the Id field's type.", "error", send_msg=True
        )
        return None

    def create_jpa_repo_file(
        self,
        buffer_path: Path,
        class_name: str,
        boiler_plate: str,
        debugger: bool = False,
    ) -> None:
        file_path = buffer_path.parent.joinpath(f"{class_name}Repository.java")
        if debugger:
            self.messaging.log(f"Class name: {class_name}", "debug")
            self.messaging.log(f"JPA repository path: {file_path}", "debug")
            self.messaging.log(f"Boiler plate: {boiler_plate}", "debug")
        if not file_path.exists():
            with open(file_path, "w") as java_file:
                java_file.write(boiler_plate)
            if file_path.exists():
                if debugger:
                    self.messaging.log(
                        "Successfuly created JPA repository file.", "debug"
                    )
                self.nvim.command(f"edit {file_path}")
                # TODO: make sure jdtls is in plugin dependencies.
                self.nvim.command("lua require('jdtls').organize_imports()")
                return
        self.messaging.log(
            "Unable to create JPA repository file.", "error", send_msg=True
        )
        return

    def create_jpa_entity_for_buffer(
        self, root_path: Path, debugger: bool = False
    ) -> None:
        buffer_path = Path(self.nvim.current.buffer.name)
        node = self.tsutil.get_node_from_path(buffer_path, debugger=debugger)
        class_name = self.tsutil.get_node_class_name(node, debugger=debugger)
        package_path = self.pathutil.get_buffer_package_path(
            buffer_path, debugger=debugger
        )
        if class_name is None:
            self.messaging.log(
                "Couldn't find the class name for this buffer.", "error", send_msg=True
            )
            return
        if not self.is_buffer_jpa_entity(node):
            self.messaging.log(
                "Current buffer isn't a JPA entity.", "error", send_msg=True
            )
            return
        if not self.buffer_has_id_field(node, debugger=debugger):
            superclass_name_node = self.get_buffer_superclass_node(
                node, debugger=debugger
            )
            if not superclass_name_node:
                self.messaging.log(
                    "No Id found for this entity and no superclass to look for it.",
                    "error",
                    send_msg=True,
                )
                return
            superclass_name = self.tsutil.get_node_text(
                superclass_name_node, debugger=debugger
            )
            superclass_node = self.find_superclass_buffer(
                root_path, superclass_name, debugger
            )
            if superclass_node is None:
                self.messaging.log(
                    "Unable to locate the superclass buffer.", "error", send_msg=True
                )
                return
            if not self.buffer_has_id_field(superclass_node, debugger=debugger):
                # TODO: Keep checking for superclasses?
                self.messaging.log(
                    "Unable to find the Id field on the superclass.",
                    "error",
                    send_msg=True,
                )
                return
            id_type = self.find_id_field_type_identifier(
                superclass_node, debugger=debugger
            )
            if id_type is None:
                self.messaging.log(
                    "Unable to find get the Id field type on the superclass.",
                    "error",
                    send_msg=True,
                )
                return
            boiler_plate = self.get_boiler_plate(
                class_name=class_name,
                package_path=package_path,
                id_type=id_type,
                debugger=debugger,
            )
            self.create_jpa_repo_file(
                buffer_path=buffer_path,
                class_name=class_name,
                boiler_plate=boiler_plate,
                debugger=debugger,
            )
