"""Incident-first passive archive with explicit coverage and optional continuations."""

from collections import Counter
import io
import time
import zipfile
import zlib

from kvk.dal.new_source_import_dal import SourceConflict
from services import recovery_evidence_bundle as bundle
from services.recovery_report import incident_report


class BoundedArchive(io.BytesIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def write(self, data):
        if self.tell() + len(data) > self.limit:
            raise SourceConflict(
                "The complete archive exceeds the attachment limit. Use detailed report parts."
            )
        return super().write(data)


class Groups:
    def __init__(self):
        self.counts = Counter()
        self.other_contributions = 0

    def add(self, key):
        if key in self.counts or len(self.counts) < 256:
            self.counts[key] += 1
        else:
            self.other_contributions += 1


def build_complete_report(service, actor, max_bytes=8388608):
    service.report_authorize(actor)
    bundle.budget(max_bytes)
    with bundle.report_request() as lease:
        return _build(service, actor, max_bytes, lease)


def _build(service, actor, max_bytes, lease):
    # Freeze independent diagnostics before any SQL wait can consume the census
    # budget. Capture time remains distinct from incident and export times.
    lease.check_active()
    service.report_authorize(actor)
    components, descriptors, identity = bundle.collect_components(lease=lease)
    with BoundedArchive(max_bytes) as output, io.BytesIO() as raw:
        return _assemble(
            service, actor, max_bytes, lease, components, descriptors, identity, output, raw
        )


def _assemble(service, actor, max_bytes, lease, components, descriptors, identity, output, raw):
    import hashlib

    groups, repairs, blockers = Groups(), Groups(), Groups()
    after = through = total = None
    count = detail_bytes = 0
    digest = hashlib.sha256()
    status, reason = "available", None
    started = bundle.utc()
    read_calls, read_seconds, projection_seconds = 0, 0.0, 0.0
    # Bound both uncompressed working memory and the actual compressed prefix.
    # A trial compressor makes a row atomic: a rejected row never moves the cursor.
    compressor = zlib.compressobj(1)
    compressed_bytes = 0

    def append_prepared(items):
        nonlocal compressor, compressed_bytes, detail_bytes, count, after, reason
        if not items:
            return
        data = b"".join(item[1] for item in items)
        trial = compressor.copy()
        emitted = len(trial.compress(data))
        closed_size = compressed_bytes + emitted + len(trial.copy().flush())
        if (
            detail_bytes + len(data) > 32 * 1024 * 1024
            or closed_size + 512 > max_bytes - 32768
            or count + len(items) > 1000000
        ):
            if len(items) > 1:
                for item in items:
                    append_prepared([item])
                return
            reason = "incident_collection_byte_bound"
            raise SourceConflict("Incident prefix bound reached.")
        raw.write(data)
        compressor = trial
        compressed_bytes += emitted
        detail_bytes += len(data)
        digest.update(data)
        for identity, _, group_key, repair_keys, blocker_keys in items:
            groups.add(group_key)
            for key in repair_keys:
                repairs.add(key)
            for key in blocker_keys:
                blockers.add(key)
            count += 1
            after = identity

    try:
        while True:
            lease.check()
            service.report_authorize(actor)
            read_started = time.perf_counter()
            read_calls += 1
            try:
                page = service.store.report_page(after=after, through=through, page_size=10)
            finally:
                read_seconds += time.perf_counter() - read_started
            through = page["through"]
            if total is None:
                total = page["total"]
            elif total != page["total"]:
                raise SourceConflict("Incident census changed during collection.")
            # An entered read remains owned even beyond the budget. Preserve its
            # bounded returned page before deciding whether to begin another read.
            lease.check_active()
            prepared, prepared_bytes, page_error = [], 0, None
            for row in page["rows"]:
                lease.check_active()
                projection_started = time.perf_counter()
                try:
                    item = incident_report(service, row)
                    data = bundle.encode(item) + b"\n"
                    if detail_bytes + prepared_bytes + len(data) > 32 * 1024 * 1024:
                        reason = "incident_collection_byte_bound"
                        raise SourceConflict("Incident staging bound reached.")
                    # All fallible row interpretation precedes byte/cursor acceptance.
                    group_key = (
                        item["source_kind"],
                        item["state"],
                        item["diagnosis"].get("outcome"),
                    )
                    repair_keys = [
                        (r["action"], r["availability"]) for r in item["required_repairs"]
                    ]
                    blocker_keys = [
                        (link["kind"], link["source_id"])
                        for link in item["diagnosis"].get("recovery_links", [])
                    ]
                    for key in [group_key, *repair_keys, *blocker_keys]:
                        hash(key)
                    prepared.append((row["IncidentID"], data, group_key, repair_keys, blocker_keys))
                    prepared_bytes += len(data)
                except Exception as error:
                    page_error = error
                    break
                finally:
                    projection_seconds += time.perf_counter() - projection_started
            # One exact compression check per bounded page normally; at a size
            # boundary fall back to rows to retain the largest fitting prefix.
            append_prepared(prepared)
            if page_error is not None:
                raise page_error
            if not page["more"]:
                break
            if not page["rows"]:
                raise SourceConflict("Incident cursor did not advance.")
            time.sleep(0.000001)
        if count != total:
            raise SourceConflict("Incident coverage changed during collection.")
    except Exception as error:
        status = "partial" if through is not None else "unavailable"
        reason = reason or (
            "incident_collection_time_bound"
            if isinstance(error, bundle.ReportBudgetExceeded)
            else "incident_collection_unavailable_or_bound"
        )
    try:
        with zipfile.ZipFile(
            output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1
        ) as archive:
            if count or status == "available":
                with raw.getbuffer() as data_view:
                    archive.writestr("incidents.jsonl", data_view)
    finally:
        raw.close()
    try:
        service.report_authorize(actor)
        output.limit = max_bytes
        lease.check_active()
        provenance = getattr(service, "report_identity", None)
        if type(provenance) is dict:
            identity.update(provenance)
        descriptors["incidents.jsonl"] = dict(
            status=status,
            reason=reason,
            included=count,
            total=total,
            available=total if total is not None else "unknown",
            omitted=total - count if total is not None else "unknown",
            cutoff_utc=str(through) if through is not None else None,
            captured_from_utc=started,
            captured_through_utc=bundle.utc(),
            collection=dict(
                read_calls=read_calls,
                read_seconds=read_seconds,
                projection_seconds=projection_seconds,
                budget_seconds=30,
            ),
        )
        descriptors["incidents.jsonl"].update(bytes=detail_bytes, sha256=digest.hexdigest())
        summary = dict(
            format="k98-recovery-complete-report-v1",
            generated_utc=bundle.utc(),
            incidents_first_seen_through_utc=str(through) if through is not None else None,
            complete=status == "available",
            included_incidents=count,
            total_recorded_incidents=total,
            coverage="All states through the cutoff. Sources are captured independently; this is not a transactional snapshot or evidence of undiscovered work.",
            groups=(
                [
                    dict(source_kind=k[0], state=k[1], outcome=k[2], count=v)
                    for k, v in groups.counts.items()
                ]
                if count
                else []
            ),
            required_repairs=(
                [dict(action=k[0], availability=k[1], count=v) for k, v in repairs.counts.items()]
                if count
                else []
            ),
            linked_recovery=(
                [
                    dict(kind=k[0], source_id=k[1], dependent_incidents=v)
                    for k, v in blockers.counts.items()
                ]
                if count
                else []
            ),
            omitted_groups=(
                "unknown" if any(g.other_contributions for g in (groups, repairs, blockers)) else 0
            ),
            other_contributions=dict(
                groups=groups.other_contributions,
                repairs=repairs.other_contributions,
                blockers=blockers.other_contributions,
            ),
        )
        summary_data = bundle.encode(summary)
        if len(summary_data) > 262144:
            summary.update(
                groups=[], required_repairs=[], linked_recovery=[], omitted_groups="unknown"
            )
            summary_data = bundle.encode(summary)
        pending = {}
        with zipfile.ZipFile(
            output, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=1
        ) as archive:
            # Preflight each optional member independently. Compression bound includes
            # headers/directory and 16 KiB for the final manifest; incidents never rescan.
            for name, data in [
                ("summary.json", summary_data),
                *[
                    (name, components[name])
                    # Keep existing evidence priority; health remains optional and
                    # uses the same bounded continuation path when it cannot fit.
                    for name in (
                        "startup.json",
                        "diagnostic-health.json",
                        "operations.jsonl",
                        "health-observations.json",
                    )
                    if name in components
                ],
            ]:
                current = descriptors.get(name, {"status": "available"})
                needed = len(zlib.compress(data, 1)) + 512
                if output.tell() + needed + 16384 <= max_bytes:
                    archive.writestr(name, data)
                    descriptors[name] = bundle.descriptor(data, **current)
                else:
                    pending[name] = data
                    if name == "summary.json":
                        minimal = dict(
                            summary,
                            groups=[],
                            required_repairs=[],
                            linked_recovery=[],
                            omitted_groups="unknown",
                            summary_continuation=True,
                        )
                        small = bundle.encode(minimal)
                        archive.writestr(name, small)
                        descriptors[name] = bundle.descriptor(
                            small, status="partial", reason="summary_detail_continuation"
                        )
                        continue
                    descriptors[name] = dict(
                        current,
                        status="partial",
                        reason="diagnostic_continuation",
                        bytes=len(data),
                        sha256=bundle.sha(data),
                    )
            token = bundle.retain(service, actor, pending, identity, descriptors)
            meta = bundle.manifest(
                descriptors,
                identity,
                diagnostic_continuation=bool(token),
                incident_continuation=status != "available",
                incident_after=after,
                cutoff_utc=str(through) if through is not None else None,
                **bundle.initial_chain(token),
            )
            if len(meta) > 32768:
                raise SourceConflict("Evidence manifest exceeds its bound.")
            archive.writestr("manifest.json", meta)
        content = output.getvalue()
        bundle.anchor_initial(token, content)
    finally:
        output.close()

    return dict(
        content=content,
        filename="K98-recovery-complete-report.zip",
        count=count,
        complete=status == "available",
        incident_continuation=status != "available",
        incident_after=after,
        total=total,
        diagnostic_token=token,
        through=through,
        sha256=bundle.sha(content),
        bytes=len(content),
    )
