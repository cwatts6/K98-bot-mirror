"""Guided abandoned-read recovery; the private authority supplies all proof."""


class ConfigReadRecoveryAdapter:
    kind = "configuration_read"
    automatic_action = "release_read"

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
        if result["eligible"] and result["outcome"] == "read_containment":
            actions["contain_read"] = dict(
                label="Isolate read & release",
                check="Confirm this failed configuration read can be discarded. The bot verified that all recorded requests are read-only. A previously dispatched read may still finish, but its result will not be used. No child termination or provider health is being asserted.",
                effect="Atomically fence further requests and release only this read's exact reservations. Preserve its original history and a verified isolation receipt, then verify the committed release so eligible work can continue.",
            )
        elif result["eligible"]:
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
        if action == "contain_read":
            return self.client.contain_configuration_recovery(source_id, token, actor, reason)
        if action != "release_read":
            raise ValueError("Unsupported configuration repair.")
        return self.client.apply_configuration_recovery(source_id, token, actor, reason)

    def reconcile(self, source_id, action):
        result = self.client.inspect_configuration_recovery(source_id)
        if result["settled_token"] == action["EvidenceHash"]:
            return "verified"
        matches_action = result["outcome"] == {
            "release_read": "abandoned_read",
            "contain_read": "read_containment",
        }.get(action.get("ActionKind"))
        if result["eligible"] and matches_action and result["token"] == action["EvidenceHash"]:
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
        if (result["eligible"] or result["outcome"] == "resolved") and (
            result["token"] != action["EvidenceHash"] or not matches_action
        ):
            return "not_applied"
        return None
