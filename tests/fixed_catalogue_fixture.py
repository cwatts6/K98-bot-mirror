"""Native-shaped fixed catalogue rows for reader ownership tests."""

from copy import deepcopy

from services.export_execution_dal import INSTALLATION_OBJECTS


def fixed_reader_rowsets(observed):
    scope = sorted(INSTALLATION_OBJECTS)
    object_ids = {name: index for index, name in enumerate(scope, 1)}
    for row in observed["metadata"]["columns"]:
        row.update(
            dict.fromkeys(
                (
                    "DefaultName",
                    "DefaultDefinition",
                    "ComputedDefinition",
                    "ComputedPersisted",
                    "IdentitySeed",
                    "IdentityIncrement",
                )
            )
        )
    columns = [
        dict(row, NativeObjectID=object_ids[row["ObjectName"]], NativeDefaultID=0)
        for row in observed["metadata"]["columns"]
    ]
    groups = [
        [row for row in columns if row["ObjectName"] in scope[offset : offset + 16]]
        for offset in range(0, len(scope), 16)
    ]
    return deepcopy(
        [
            observed["migrations"],
            observed["metadata"]["objects"],
            *groups,
            [],
            [],
            [],
            *(
                observed["metadata"][key]
                for key in ("indexes", "checks", "foreign_keys", "triggers")
            ),
            observed["permissions"],
        ]
    )
