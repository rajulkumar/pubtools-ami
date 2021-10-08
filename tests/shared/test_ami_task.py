import pytest
from mock import patch

from pubtools._ami.task import AmiTask

step = AmiTask.step


class TestAmiTask(AmiTask):
    def add_args(self):
        super(TestAmiTask, self).add_args()
        self.parser.add_argument("--skip", help="skip a step")

    @step("task1")
    def task1(self):
        print("task1")

    @step("task2")
    def task2(self):
        print("task2")

    def run(self):
        self.task1()
        self.task2()


def test_skip(capsys):
    task = TestAmiTask()
    arg = ["", "--skip", "task1"]
    with patch("sys.argv", arg):
        task.main()

    out, _ = capsys.readouterr()
    assert "task2" in out
    assert "task1" not in out


def test_task_run():
    task = AmiTask()
    with pytest.raises(NotImplementedError):
        task.run()
