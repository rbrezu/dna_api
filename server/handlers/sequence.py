import io
import os
import tempfile
import traceback
from datetime import datetime
import json
import re
from collections import OrderedDict
from concurrent.futures.process import ProcessPoolExecutor

from Bio import SeqIO, Alphabet
from pymongo import MongoClient
from tornado.web import HTTPError

from server.handlers import ApiHandler
from tornado import gen

from server.index.sequence_index import SequenceIndex
from server.json_encoder import Encoder
from server.utils import logger


def recreate_idx(db_url, db, file_path, idx_dir):
    pymongo_client = MongoClient(db_url, connectTimeoutMS=2)
    db = pymongo_client[db]
    try:
        seqs = list(SeqIO.parse(file_path, 'fasta'))
        idx = SequenceIndex()

        size = len(seqs)

        db.job.save({
            '_id': 'index_job',
            'status': 'STARTING',
            'file': file_path,
            'no_seqs': size - 1,
            'current_seq': 0,
            'message': 'Started indexing job'
        })

        for index, row in enumerate(seqs):
            name, sequence = row.id, str(row.seq)
            db.sequence.insert({
                'sequence_id': name,
                'tags': row.description,
                'sequence': sequence,
                'sequence_size': len(sequence),
                'last_modified_date': datetime.now()
            })

            idx.add({'name': name, 'sequence': sequence})

            db.job.update({'_id': 'index_job'}, {'$set': {'current_seq': index,
                                                          'message': 'We are at {}/{} from the indexing process'.format(
                                                              index, size),
                                                          'percent': round((index + 1) / size * 50 + 15)}})

        db.job.update({'_id': 'index_job'}, {
            '$set': {'status': 'FINISHED_INSERT', 'message': 'Saving index to disk... this may take a while',
                     'percent': 70}})

        idx.save('idx_new')
        os.replace(os.path.join(idx_dir, 'idx_new.pk'), os.path.join(idx_dir, 'idx.pk'))

        db.job.update({'_id': 'index_job'},
                      {'$set': {'status': 'FINISHED_SAVE', 'message': 'Saved index to disk', 'percent': 80}})
    except:
        print(traceback.format_exc())
        db.job.update({'_id': 'index_job'}, {'$set': {'status': 'FAILED', 'message': 'Failed job', 'percent': 100}})


class SequenceUploadHandler(ApiHandler):
    executor = ProcessPoolExecutor(max_workers=1)

    @gen.coroutine
    def get(self):
        job = yield self.job_repository.find_one({'_id': 'index_job'}, process_query=False)
        if job and job['status'] != 'FAILED' and job['status'] != 'DONE':
            self.write_json(job, 206)
            return

        self.set_status(200)

    @gen.coroutine
    def post(self):
        job = yield self.job_repository.find_one({'_id': 'index_job'}, process_query=False)
        if job and job['status'] != 'FAILED' and job['status'] != 'DONE':
            self.write_json(job, 206)
            return

        file = self.request.files['file'][0]
        yield self.job_repository.save({'_id': 'index_job', 'status': 'SAVING_FILE', 'percent': 15})

        self.finish()

        dirpath = tempfile.mkdtemp()
        f = open(os.path.join(dirpath, 'file.fa'), 'wb')
        f.write(file.body)
        f.close()

        yield self.executor.submit(recreate_idx,
                                   self.context.config.MONGODB_URL,
                                   self.context.config.MONGODB_DATABASE,
                                   f.name,
                                   self.context.config.INDEX_DIR)

        yield self.job_repository.update({'_id': 'index_job'}, {
            '$set': {'status': 'RELOADING_INDEX', 'message': 'Reloading index', 'percent': 85}}, process_query=False)
        SequenceIndex().load(self.context.config.INDEX_DIR, force=True)
        yield self.job_repository.update({'_id': 'index_job'}, {'$set': {'status': 'DONE', 'percent': 100}},
                                         process_query=False)

        self.set_status(201)


class SequenceQueryHandler(ApiHandler):
    @gen.coroutine
    def post(self):
        body = json.loads(self.request.body.decode('utf-8'))

        if 'seq' not in body:
            raise HTTPError(400, 'You must have a sequence to query against')

        idx = SequenceIndex()
        found = idx.find({'sequence': body['seq']}, body.get('dist', 100))

        logger.debug('Found {} hits from index'.format(len(found)))
        items_dict = OrderedDict()

        for distance, item in found:
            items_dict[item['name']] = distance

        seqs = yield self.sequence_repository.find({
            'sequence_id': {'$in': list(items_dict.keys())}
        })
        seq_dict = {seq['sequence_id']: {**seq, 'distance': items_dict[seq['sequence_id']]} for seq in seqs}

        self.write_json([seq_dict[key] for key in items_dict.keys()])
