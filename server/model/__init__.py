import datetime
import json
import types
from functools import wraps

import pymongo
import tornado.gen as gen
from bson import ObjectId
from cerberus import Validator
from tornado import web
from tornado.web import HTTPError


class ValidatorError(web.HTTPError):
    def __init__(self, message, validator_error_list):
        self.status_code = 405
        self.log_message = message
        self.validator_errors = validator_error_list
        self.reason = 'Validation error'

    def __str__(self):
        message = "HTTP %d: %s" % (
            self.status_code,
            self.reason)
        if self.log_message:
            return message + " (" + self.log_message + ")"
        else:
            return message


class BaseModel(object):
    """
    Base Model class that accomplishes translation from
    the database layer to the service layer.

    Uses cerber library to validate service layer objects when
    doing the mapping.
    """
    DefaultSchema = {}

    def update_fields(self, *args, **kwargs):
        self.update_value('created_by', kwargs.get('principal', 'system'))
        self.update_value('created_date', datetime.datetime.now())

    def mandatory_fields_update(self, *args, **kwargs):
        self.update_id()
        self.update_value('last_modified_by', kwargs.get('principal', 'system'), True)
        self.update_value('last_modified_date', datetime.datetime.now(), True)

    def __init__(self, dictionary, validate=False, principal=None, update_fields=True,
                 schema=None, allow_unknown=False, purge_unknown=False):
        self.__dict__ = dictionary
        if validate:
            self.__dict__ = self.validate(schema, allow_unknown, purge_unknown)

        if update_fields:
            self.update_fields(principal=principal)
            self.mandatory_fields_update(principal=principal)

    def validate(self, schema=None, allow_unknown=False, purge_unknown=False):
        schema = schema if schema else self.DefaultSchema
        validator = Validator(schema, allow_unknown=allow_unknown, purge_unknown=purge_unknown)

        is_valid = validator.validate(self.__dict__)
        if not is_valid:
            raise ValidatorError('Validation failed', validator.errors)

        return validator.normalized(self.__dict__)

    @classmethod
    def return_model_dict(cls, dictionary, validate=False, principal=None, update_fields=True,
                          schema=None, allow_unknown=False, purge_unknown=False):
        if not dictionary:
            return None

        model_object = cls(dictionary, validate=validate, principal=principal,
                           update_fields=update_fields, schema=schema, allow_unknown=allow_unknown,
                           purge_unknown=purge_unknown)
        return model_object.__dict__

    @classmethod
    def from_json(cls, json_object, validate=False, principal=None, multi=False, update_fields=True,
                  schema=None, allow_unknown=False, purge_unknown=False):
        if not json_object:
            return None

        if multi:
            return list(map(
                lambda dictionary: cls.return_model_dict(dictionary, validate=validate,
                                                         principal=principal, update_fields=update_fields,
                                                         schema=schema, allow_unknown=allow_unknown,
                                                         purge_unknown=purge_unknown),
                json.loads(json_object)))

        return cls.return_model_dict(json.loads(json_object), validate=validate,
                                     principal=principal, update_fields=update_fields, schema=schema,
                                     allow_unknown=allow_unknown, purge_unknown=purge_unknown)

    @classmethod
    def from_dict(cls, dictionary, validate=False, principal=None, update_fields=True, schema=None,
                  allow_unknown=False, purge_unknown=False):
        return cls.return_model_dict(dictionary, validate=validate, principal=principal,
                                     update_fields=update_fields, schema=schema, allow_unknown=allow_unknown,
                                     purge_unknown=purge_unknown)

    def update_value(self, key, value, force=False):
        if value and (key not in self.__dict__ or force):
            self.__dict__[key] = value

    def update_id(self):
        if '_id' in self.__dict__ and not isinstance(self.__dict__['_id'], ObjectId):
            self.__dict__['_id'] = ObjectId(self.__dict__['_id'])


def wrapper(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymongo.errors.DuplicateKeyError:
            raise HTTPError(400, reason='Object already exists')
        except Exception as e:
            raise e

    return wrapped


class BaseRepository:
    '''
    Base repository for interaction with pymotor
    Implements basic repository functions.
    '''

    def __init__(self, models, database, context):
        self.context = context
        self.model = models[self.collection_name]
        self.repo = database[self.collection_name]

    def __getattr__(self, name):
        # WRAPPING REPOSITORY ERRORS
        attr = super(BaseRepository, self).__getattribute__(name)
        if isinstance(type(attr), types.MethodType):
            attr = wrapper(attr)

        return attr

    @gen.coroutine
    def find_one(self, *args, **kwargs):
        """
        Get a document from the database.

        All arguments to :meth:`find` are also valid arguments for
        :meth:`find_one`. Returns a single document, or ``None`` if no matching
        document is found.
        """
        result = yield self.find(*args, **kwargs, just_one=True)
        return result

    @gen.coroutine
    def find(self, query, just_one=False, sort=None, limit=None, skip=None, project=None,
             process_query=True, principal=None, update_fields=False, validate=False, schema=None, join_refs=False,
             refs=None):
        """
        Get multiple document from the database.

        :Parameters:
        Most parameters are direct association to pymongo:find
        Special parameters:
        :parameter principal - the user doing the operation
        :parameter just_one - return just one from cursor
        :parameter update_fields - update last_modifed_date and last_modified_by fields
        :parameter validate - validate model returned from the repository
        :parameter schema - validation schema
        :parameter join_refs - join any db_refs inside the document

        :returns a list of documents
        """

        if process_query:
            self.process_query(query)

        if just_one:
            result = yield self.repo.find_one(query, project)
            result = yield self.join_db_refs(result, join_refs=join_refs, just_one=just_one, refs=refs)

            return self.model.from_dict(result, principal=principal,
                                        update_fields=update_fields, validate=validate,
                                        schema=schema) if result else None

        cursor = self.repo.find(query, project)
        if sort:
            field, direction = sort
            cursor.sort(field, direction)

        if limit:
            cursor.limit(limit)

        if skip:
            cursor.skip(skip)

        results = []
        while (yield cursor.fetch_next):
            results.append(
                self.model.from_dict(
                    cursor.next_object(), principal=principal, update_fields=update_fields,
                    validate=validate, schema=schema
                )
            )

        results = yield self.join_db_refs(results, join_refs=join_refs, just_one=just_one, refs=refs)
        return results

    @gen.coroutine
    def count(self, query, process_query=True):
        """
        Returns the count of documents from query

        :param query:
        :param process_query:
        :return:
        """

        if process_query:
            self.process_query(query)

        n = yield self.repo.count_documents(query)
        return n

    @gen.coroutine
    # return_document = True - After | False - Before
    def find_and_update(self, query, update, project=None, return_document=True,
                        process_query=True, principal=None, update_fields=True, upsert=False, validate=False,
                        schema=None, join_refs=False, refs=None):
        """
        Find and update one document from the database.

        :Parameters:
        Most parameters are direct association to pymongo:find_one_and_update

        :Special parameters:
        :parameter principal: - the user doing the operation
        :parameter just_one: - return just one from cursor
        :parameter update_fields: - update last_modifed_date and last_modified_by fields
        :parameter validate: - validate model returned from the repository
        :parameter schema: - validation schema
        :parameter join_refs: - join any db_refs inside the document
        :return:
        """
        if process_query:
            self.process_query(query)

        result = yield self.repo.find_one_and_update(query, update, projection=project, return_document=return_document,
                                                     upsert=upsert)
        result = yield self.join_db_refs(result, join_refs=join_refs, just_one=True, refs=refs)

        return self.model.from_dict(result, principal=principal, update_fields=update_fields,
                                    validate=validate, schema=schema)

    @gen.coroutine
    def _insert_or_replace_one(self, document):
        """
        Either inserts a document if no _id is found or updates the document with
        the given _id.
        """

        if '_id' in document:
            yield self.repo.replace_one({'_id': document['_id']}, document, True)
            return document
        else:
            insert_result = yield self.repo.insert_one(document)
            result = insert_result.inserted_id
            document['_id'] = result
            return document

    @gen.coroutine
    def save(self, to_insert, join_refs=False, refs=None, project=None):
        """
        Simulate a save in mongodb by either inserting if no _id is found,
        or updating a document.
        Uses internal function :self._insert_or_replace_one:.

        :Parameters:
        Most parameters are direct association to pymongo:insert and pymongo:update
        :return:
        """

        if not project:
            project = {}

        if not isinstance(to_insert, list):
            self.on_pre_save(to_insert)
            to_insert = yield self._insert_or_replace_one(to_insert)

            self.on_post_save(to_insert)
        elif to_insert:
            results = []
            for insert in to_insert:
                rez = yield self.save(insert, project=project)
                results.append(rez)

            results = yield self.join_db_refs(results, join_refs=join_refs, just_one=False, refs=refs)
            return results

        projected = {'_id': to_insert['_id']} if 1 in project.values() else to_insert
        for key, value in project.items():
            if value == 1:
                if key in to_insert:
                    projected.update({key: to_insert[key]})

            if value == 0:
                projected.pop(key, None)

        result = yield self.join_db_refs(projected, join_refs=join_refs, just_one=True, refs=refs)
        return result

    @gen.coroutine
    def update(self, query, update, just_one=True, process_query=True):
        """
        Run an update command on document matched by query

        :parameter update: update query
        :parameter query: query object

        :return:
        """

        if process_query:
            self.process_query(query)

        if just_one:
            # old_document = yield self.repo.find_one(query)
            # _id = old_document['_id']

            result = yield self.repo.update_one(query, update)
            # new_document = yield self.repo.find_one({'_id': _id}) # timeit: maybe return idk ?

            return result

        result = yield self.repo.update_many(query, update)
        return result

    @gen.coroutine
    def remove(self, query, process_query=True):
        """
        Delete all documents matching query

        :parameter query: query object

        :return:
        """
        if process_query:
            self.process_query(query)

        self.on_pre_delete(query)

        result = yield self.repo.delete_many(query)
        return result.deleted_count

    @gen.coroutine
    def aggregate(self, pipeline):
        self.process_query(pipeline)
        cursor = self.repo.aggregate(pipeline)

        results = []
        while (yield cursor.fetch_next):
            results.append(
                self.model.from_dict(
                    cursor.next_object()
                )
            )

        return results

    @gen.coroutine
    def join_db_refs(self, objects, join_refs=False, just_one=True, refs=None):
        if not refs:
            refs = self.model.refs if hasattr(self.model, 'refs') else None

        if not join_refs or not objects or not refs:
            return objects

        if just_one:
            for ref in refs:
                field = ref['field']
                dest = ref['dest']
                collection = ref['collection']
                fmt = ref['fmt']
                project = ref['project']

                if field in objects:
                    item = yield self.context.repositories[collection] \
                        .find({'_id': fmt(objects[field])}, just_one=just_one, process_query=False, project=project)
                    objects[dest] = item
            return objects

        # Best item parsing O(refs * n * log n) + O(n) ... TODO: FASTER?
        item_dict = {}
        for ref in refs:
            field = ref['field']
            collection = ref['collection']
            fmt = ref['fmt']
            project = ref['project']

            item_dict[field] = {}

            ids = {fmt(object[field]) for object in objects}
            ids.remove(None)

            items = yield self.context.repositories[collection] \
                .find({'_id': {'$in': ids}}, just_one=just_one, process_query=False, project=project)

            for item in items:
                item_dict[field][item['_id']] = item

        for object in objects:
            for ref in refs:
                dest = ref['dest']
                field = ref['field']
                fmt = ref['fmt']

                if field in object:
                    old = object[field]
                    object[dest] = item_dict[field][fmt(old)]

        return objects

    def process_query(self, query):
        if '_id' in query and not isinstance(query['_id'], ObjectId):
            if isinstance(query['_id'], dict) and '$in' in query['_id']:
                query['_id'] = {'$in': [ObjectId(_id) for _id in query['_id']['$in']]}
            elif isinstance(query['_id'], str):
                query['_id'] = ObjectId(query['_id'])

    def on_pre_save(self, object):
        pass

    def on_post_save(self, object):
        pass

    def on_pre_delete(self, query):
        pass

    def on_post_delete(self, query):
        pass
