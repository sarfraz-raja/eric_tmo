import os
import logging


class Custom_Log:
    def __init__(self, log_file='test_custom_logs.txt', activity='', level=logging.DEBUG):
        log_dir = os.path.dirname(log_file)
        if log_dir: os.makedirs(log_dir, exist_ok=True)
        log = logging.getLogger(__name__)
        log.setLevel(level)
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter(F'{activity} --%(asctime)s -- %(name)s -- %(message)s')
        fh.setFormatter(formatter)
        log.addHandler(fh)
        self.log = log

    def release(self):
        for handler in self.log.handlers[:]:
            handler.close()
            self.log.removeHandler(handler)
