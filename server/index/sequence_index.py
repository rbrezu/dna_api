import os

import dill
import editdistance
import pybktree

import enum
from server.utils import Singleton

class SequenceIndex(metaclass=Singleton):
    def __init__(self):
        self.loaded = False

    def load(self, idx_dir, force=False):
        if self.loaded and not force:
            return

        self.idx_dir = idx_dir
        self.file_path = os.path.join(idx_dir, 'idx.pk')
        if os.path.exists(self.file_path):
            with open(self.file_path, 'rb') as file:
                self.tree = dill.load(file)
        else:
            self.tree = pybktree.BKTree(lambda x, y: editdistance.eval(x['sequence'], y['sequence']))

        self.loaded = True
        self.tree.distance_func = lambda x, y: editdistance.eval(x['sequence'], y['sequence'])

    def save(self, idx_file='idx'):
        with open(os.path.join(self.idx_dir, '{}.pk'.format(idx_file)), 'wb') as file:
            dill.dump(self.tree, file)

    def add(self, item):
        self.tree.add(item)

    def find(self, item, edit_distance=50):
        return self.tree.find(item, edit_distance)
