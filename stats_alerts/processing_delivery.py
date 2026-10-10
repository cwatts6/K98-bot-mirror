"""Durable per-component observation around the existing stats routing/guards."""

from services.legacy_export_snapshot_service import drain_thread
from services.processing_notification_store import NotificationHeld
from stats_alerts.delivery_outcomes import DeliveryTracker


class DurableStatsTracker(DeliveryTracker):
    durable = True

    def __init__(self, store, run_id):
        super().__init__("seasonal")
        self.store = store
        self.run_id = run_id
        self.correlation_id = run_id

    async def before_dispatch(self, channel_id=None, *, operation="send", message_id=None):
        await drain_thread(
            self.store.enter,
            self.run_id,
            self.attempts[-1].component,
            channel_id=channel_id,
            operation=operation,
            message_id=message_id,
            route=self.route,
        )
        self.enter(channel_id, operation=operation, message_id=message_id)

    async def after_dispatch(self, message, channel=None, *, operation="send"):
        self.receipt(message, channel, operation=operation)
        item = self.attempts[-1]
        if not item.acknowledged:
            raise NotificationHeld("Discord returned no exact message receipt.")
        await drain_thread(
            self.store.acknowledge,
            self.run_id,
            item.component,
            message_id=item.message_id,
            channel_id=item.channel_id,
        )

    async def finish(self):
        def record(row):
            for item in self.attempts:
                existing = row["components"].get(item.component)
                if existing and existing["state"] in {"acknowledged", "skipped", "held"}:
                    continue
                if existing and existing["state"] == "sending":
                    if item.entered:
                        existing.update(state="held", reason="send_acknowledgment_unproven")
                elif item.outcome == "skipped":
                    row["components"][item.component] = dict(state="skipped", reason=item.reason)
                else:
                    row["components"][item.component] = dict(state="failed", reason=item.reason)
            stats_items = [
                v for k, v in row["components"].items() if not k.startswith(("sheets_", "summary_"))
            ]
            row["stats_delivery"] = (
                "held"
                if any(v["state"] in {"sending", "held"} for v in stats_items)
                else (
                    "complete"
                    if stats_items
                    and all(v["state"] in {"acknowledged", "skipped"} for v in stats_items)
                    else "retry_pending"
                )
            )

        await drain_thread(self.store.update, self.run_id, record)
