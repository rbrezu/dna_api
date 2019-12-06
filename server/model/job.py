from server.model import BaseModel, BaseRepository


class JobModel(BaseModel):
    DefaultSchema = {}


class JobRepository(BaseRepository):
    collection_name = 'job'
