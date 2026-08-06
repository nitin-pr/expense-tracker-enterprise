from common.repositories.base import BaseRepository


class BaseService:
    def __init__(self, repository: BaseRepository):
        self.repository = repository