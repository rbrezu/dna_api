from server.model import BaseModel, BaseRepository


class SequenceModel(BaseModel):
    DefaultSchema = {
        '_id': {'type': 'string'},
        'sequence_id': {'required': True, 'type': 'string'},
        'type': {'required': True, 'type': 'string'},
        'extra': {'type': 'dict'},
        'sequence': {'required': True, 'type': 'string'},
        'sequence_size': {'required': True, 'type': 'integer'},
        'description': {'required': True, 'type': 'string'}
    }


class SequenceRepository(BaseRepository):
    collection_name = 'sequence'
