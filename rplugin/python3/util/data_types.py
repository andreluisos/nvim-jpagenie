from typing import Literal

CollectionType = Literal["set", "list", "collection"]
FetchType = Literal["lazy", "eager"]
MappingType = Literal["unidirectional_join_column", "bidirectional_join_column"]
CascadeType = Literal["all", "persist", "merge", "remove", "refresh", "detach"]
SelectedOther = Literal["mandatory", "unique", "orphan_removal", "large_object"]
FieldTimeZoneStorage = Literal["NATIVE", "NORMALIZE", "NORMALIZE_UTC", "COLUMN", "AUTO"]
FieldTemporal = Literal["DATE", "TIME", "TIMESTAMP"]