"""Authorized season setup independent of Discord and serving configuration."""

from kvk.dal.season_source_dal import SeasonSourceDAL


class SeasonSourceService:
    def __init__(self, connect):
        self.dal = SeasonSourceDAL(connect)

    def choose(self, kvk_no, source_key, **authority):
        return self.dal.choose(kvk_no, source_key, **authority)

    def read(self, kvk_no):
        return self.dal.read(kvk_no)

    def transition(self, kvk_no, state, **authority):
        return self.dal.transition(kvk_no, state, **authority)
