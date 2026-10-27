"""One download containing all recorded incidents and their complete summary."""

from collections import Counter
from datetime import UTC, datetime
import io
import json
import zipfile

from kvk.dal.new_source_import_dal import SourceConflict
from services import recovery_health
from services.recovery_report import encode, incident_report


class BoundedArchive(io.BytesIO):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def write(self, data):
        if self.tell() + len(data) > self.limit:
            raise SourceConflict(
                "The complete archive exceeds this channel's attachment limit. Use the detailed report parts; no incidents were silently omitted."
            )
        return super().write(data)


def build_complete_report(service, actor, max_bytes=8388608):
    service.authorize(actor)
    if type(max_bytes) is not int or not 65536 <= max_bytes <= 8 * 1024 * 1024:
        raise SourceConflict("A supported attachment budget is required.")
    output = BoundedArchive(max_bytes)
    groups, repairs, blockers = Counter(), Counter(), Counter()
    after = through = None
    count = 0
    detail_bytes = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        with archive.open("incidents.jsonl", "w") as detail:
            while True:
                page = service.store.report_page(after=after, through=through)
                through = page["through"]
                for row in page["rows"]:
                    item = incident_report(service, row)
                    encoded = (
                        json.dumps(item, ensure_ascii=False, allow_nan=False).encode("utf-8")
                        + b"\n"
                    )
                    detail_bytes += len(encoded)
                    if detail_bytes > 128 * 1024 * 1024:
                        raise SourceConflict(
                            "The complete details exceed the 128 MiB collection bound. Use detailed report parts; no incidents were silently omitted."
                        )
                    detail.write(encoded)
                    groups[
                        (item["source_kind"], item["state"], item["diagnosis"].get("outcome"))
                    ] += 1
                    for repair in item["required_repairs"]:
                        repairs[(repair["action"], repair["availability"])] += 1
                    for link in item["diagnosis"].get("recovery_links", []):
                        blockers[(link["kind"], link["source_id"])] += 1
                    count += 1
                    after = row["IncidentID"]
                if not page["more"]:
                    break
                if not page["rows"] or count >= 1000000:
                    raise SourceConflict(
                        "Report collection did not complete within its bound. No complete report was issued."
                    )
        summary = dict(
            format="k98-recovery-complete-report-v1",
            generated_utc=datetime.now(UTC).isoformat(),
            incidents_first_seen_through_utc=str(through),
            complete=count == page["total"],
            included_incidents=count,
            total_recorded_incidents=page["total"],
            coverage="All recorded incidents through the cutoff, including resolved incidents. Observations may change during collection; this is not a transactional snapshot or proof that undiscovered failures do not exist.",
            monitor=recovery_health.report(),
            groups=[
                dict(source_kind=k[0], state=k[1], outcome=k[2], count=v) for k, v in groups.items()
            ],
            required_repairs=[
                dict(action=k[0], availability=k[1], count=v) for k, v in repairs.items()
            ],
            linked_recovery=[
                dict(kind=k[0], source_id=k[1], dependent_incidents=v) for k, v in blockers.items()
            ],
            details="incidents.jsonl contains every included incident, diagnosis, blocker link, repair requirement and verification state.",
        )
        if not summary["complete"]:
            raise SourceConflict(
                "Incident coverage changed during collection. Download again; no incomplete archive was presented as complete."
            )
        archive.writestr("summary.json", encode(summary))
    return dict(content=output.getvalue(), filename="K98-recovery-complete-report.zip", count=count)
