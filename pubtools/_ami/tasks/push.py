import logging

from pubtools._ami.task import AmiTask

LOG = logging.getLogger("pubtools.ami")

class AmiPush(AmiTask):
    def add_args(self):
        super(AmiPush, self).add_args()

        group = self.parser.add_argument_group("AMI Push arguments")

        group.add_argument()

    def run(self):
        pass


def entry_point(cls=AmiPush):
    cls.main()

def doc_parser():
    return AmiTask().parser
