from event_calendar.sql_lifecycle import SqlSession


class Connection:
    def __init__(self, *, commit_error=False, close_error=False, rollback_error=False):
        self.commit_error = commit_error
        self.close_error = close_error
        self.rollback_error = rollback_error
        self.calls = []

    def commit(self):
        self.calls.append("commit")
        if self.commit_error:
            raise RuntimeError("lost reply")

    def rollback(self):
        self.calls.append("rollback")
        if self.rollback_error:
            raise RuntimeError("rollback reply lost")

    def close(self):
        self.calls.append("close")
        if self.close_error:
            raise RuntimeError("close unconfirmed")


def test_commit_success_survives_close_failure():
    connection = Connection(close_error=True)
    session = SqlSession(lambda: connection)
    with session:
        session.commit()
    assert session.outcome.effect == "committed"
    assert session.outcome.cleanup == "unconfirmed"
    assert session.outcome.retained_connection is connection
    assert connection.calls == ["commit", "close"]
    assert "retained_connection" not in session.outcome.public()


def test_lost_commit_reply_not_proved_rolled_back():
    connection = Connection(commit_error=True)
    session = SqlSession(lambda: connection)
    try:
        with session:
            session.commit()
    except RuntimeError:
        pass
    assert session.outcome.effect == "unknown"
    assert session.outcome.rollback == "confirmed"
    assert session.outcome.cleanup == "settled"
    assert connection.calls == ["commit", "rollback", "close"]


def test_statement_failure_rollback_and_close_independent():
    for rollback_error in (False, True):
        connection = Connection(rollback_error=rollback_error)
        session = SqlSession(lambda: connection)
        try:
            with session:
                raise ValueError("private row data")
        except ValueError:
            pass
        assert session.outcome.effect == ("unknown" if rollback_error else "rolled_back")
        assert session.outcome.cleanup == "settled"
        assert session.outcome.error == {"error_type": "ValueError"}
        assert connection.calls == ["rollback", "close"]
