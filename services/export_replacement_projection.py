"""Project queued destinations through an authenticated activation prefix."""

from kvk.dal.new_source_import_dal import SourceConflict


def project_destinations(targets, mappings):
    result = {target: target for target in targets}
    seen = {target: {target} for target in targets}
    for mapping in mappings:
        for original, current in result.items():
            if current not in mapping:
                continue
            replacement = mapping[current]
            if replacement in seen[original]:
                raise SourceConflict("Queued replacement destinations contain a cycle.")
            seen[original].add(replacement)
            result[original] = replacement
    if len(set(result.values())) != len(result):
        raise SourceConflict("Queued replacement destinations collide.")
    return result


def continuation_activation(history, *, targets, consumer, anchor_id=None):
    """History is private-receipt verified by the authority before this call."""
    prefix = []
    for activation in history:
        prefix.append(activation)
        if activation["activation_id"] == anchor_id:
            break
    if not prefix or (anchor_id and prefix[-1]["activation_id"] != anchor_id):
        raise SourceConflict("The queued continuation activation is unavailable.")
    anchor = prefix[-1]
    mapping = project_destinations(targets, [a["mapping"] for a in prefix])
    if consumer == "new_source":
        matches = [
            pool
            for pool in anchor["registration"]["pools"]
            if set(mapping.values()) == {pool["index_file_id"], *pool["slot_file_ids"]}
        ]
        registered = len(matches) == 1 and all(old != new for old, new in mapping.items())
    else:
        scope = anchor["registration"]["legacy_configuration"].get(consumer)
        registered = scope and set(mapping.values()) <= set(scope["destinations"])
    if not registered:
        raise SourceConflict("Queued destinations escape the authenticated current registration.")
    if all(old == new for old, new in mapping.items()):
        raise SourceConflict("Queued continuation has no replaced output.")
    return dict(anchor, mapping=mapping, queued_continuation=True)
