"""Guided abandoned-read recovery; the private authority supplies all proof."""


class ConfigReadRecoveryAdapter:
    kind = "configuration_read"

    def __init__(self, dal, client, *, account, storage_owner):
        self.dal, self.client = dal, client
        self.account, self.storage_owner = account, storage_owner

    def pending_recovery(self, *, after=None):
        return self.dal.pending_recovery(
            account=self.account, storage_owner=self.storage_owner, after=after
        )

    def inspect(self, source_id):
        result = self.client.inspect_configuration_recovery(source_id)
        actions = {}
        if result["eligible"]:
            actions["release_read"] = dict(
                label="Release abandoned read",
                check="Confirm that this failed configuration read should be closed. The bot has verified that its complete request history contains no writes.",
                effect="Reverify the authority journal and exact reservations, release only this abandoned read, then verify the committed release. Eligible queued work can continue.",
            )
        evidence = dict(
            title="Configuration read recovery",
            outcome=result["outcome"],
            explanation=result["explanation"],
            actions=actions,
        )
        return evidence, result["token"], result["outcome"] == "resolved"

    def execute(self, source_id, action, token, actor, reason):
        if action != "release_read":
            raise ValueError("Unsupported configuration repair.")
        return self.client.apply_configuration_recovery(source_id, token, actor, reason)

    def reconcile(self, source_id, action):
        result = self.client.inspect_configuration_recovery(source_id)
        if result["settled_token"] == action["EvidenceHash"]:
            return "verified"
        if result["eligible"] and result["token"] == action["EvidenceHash"]:
            self.execute(
                source_id,
                action["ActionKind"],
                action["EvidenceHash"],
                "recovery:" + str(action["ActionID"]),
                action["Reason"],
            )
            return "verified"
        # Changed SQL evidence makes the original compare-and-set inapplicable.
        # The authority serialises inspect/apply and rechecks exact SQL ownership.
        if (result["eligible"] or result["outcome"] == "resolved") and result["token"] != action[
            "EvidenceHash"
        ]:
            return "not_applied"
        return None
