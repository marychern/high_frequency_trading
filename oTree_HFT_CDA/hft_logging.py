import csv
from .utility import nanoseconds_since_midnight as labtime
import os
from datetime import datetime
from .row_formatters import *

author = 'hasan ali demirci'


# TODO: move this to redis. There are many good reasons to do that.

class SessionEvents:

    dispatch = {
        'stage enter': format_senter,
        'stage replace': format_sreplace,
        'stage cancel': format_scancel,
        'confirm enter': format_center,
        'confirm replace': format_creplace,
        'confirm cancel': format_ccancel,
        'confirm execution': format_cexec,
        'orders in market': format_orders,
    }

    def __init__(self):
        self.backup = list()
        self.raw_logs = list()
        self.string_logs = list()
        self.columns = ['time','group','player', 'event', 'context']
        self.dirr = os.path.join(os.getcwd())
        self.prefix = 'hft_cda'
        self.set_dump_path()
    
    def set_dump_path(self):
        today = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = self.prefix + '_' + today + '.csv'
        self.path = os.path.join(self.dirr, filename)
        print(self.path)

    def push(self, processor, **kwargs):
        raw_log = processor(**kwargs)
        self.raw_logs.append(raw_log)
    
    def form(self, row):
        out = row
        if isinstance(row['context'], dict):
            event = row['event']
            out = self.__class__.dispatch[event](row)
        return out
    
    def convert(self):
        self.string_logs = [self.form(row) for row in self.raw_logs]
        self.backup.extend(self.raw_logs)
        self.raw_logs = list()

    def dump(self, header=False):
        # TODO: This is really odd.
        with open(self.path, 'a') as f:
            writer = csv.DictWriter(f, self.columns)
            if header:
                writer.writeheader()
            writer.writerows(self.string_logs)

logger = SessionEvents()