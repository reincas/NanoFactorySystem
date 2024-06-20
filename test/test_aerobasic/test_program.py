import threading
from pathlib import Path
from unittest import TestCase

from nanofactorysystem.aerobasic import Axis
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.utils.visualization import read_file, plot_movements

FOLDER = Path(__file__).parent.parent / "_programs"


class TestAeroBasicProgramManual(TestCase):
    def test_simple_program(self):
        programm = AeroBasicProgram()

        programm.ENABLE(Axis.XY)
        programm.HOME(Axis.XY)

        programm.write(FOLDER / "manual.pgm")


class AeroBasicProgramTest(TestCase):
    @classmethod
    def setUpClass(cls):
        import matplotlib
        matplotlib.use('Agg')  # Use the Agg backend

    def setUp(self):
        self.desired_content = None
        self.program = AeroBasicProgram()

    def tearDown(self):
        # Check content
        if self.desired_content is not None:
            content = self.program.to_text()
            self.assertEqual(self.desired_content, content)

        path = FOLDER / self.__class__.__name__ / f"{self._testMethodName}.txt"
        path.parent.mkdir(exist_ok=True, parents=True)
        content = self.program.write(path)
        print(f"{len(content.splitlines())} lines written")

        thread = threading.Thread(target=lambda: _write_plot(path), daemon=False)
        thread.start()


def _write_plot(path: Path):
    print(f"Creating plot for {path}")
    try:
        movements = read_file(path)
        fig = plot_movements(movements)
        fig.tight_layout()
        fig.savefig(path.with_suffix(".png"))
    except:
        print(f"Failed to create plot for {path}!")
        raise


class TestSimpleAeroBasicProgram(AeroBasicProgramTest):
    def test_simple_program(self):
        self.program.ENABLE(Axis.XY)
        self.program.HOME(Axis.XY)

        self.desired_content = ("ENABLE X Y\n"
                                "HOME X Y\n"
                                "END PROGRAM\n")

    def test_write_simple_program_str(self):
        self.test_simple_program()
        path = f"{FOLDER}/{self._testMethodName}.pgm"
        Path(path).parent.mkdir()
        self.program.write(path)

        # Check content
        self.assertEqual(self.desired_content, Path(path).read_text())

    def test_write_simple_program_pathlib(self):
        self.test_simple_program()
        path = Path(f"{FOLDER}/{self._testMethodName}.pgm")
        Path(path).parent.mkdir()
        self.program.write(path)

        # Check content
        self.assertEqual(self.desired_content, Path(path).read_text())

    def test_simple_variable(self):
        my_var = self.program.create_variable("my_var")
        my_var.set(5)

        self.desired_content = ("DVAR $my_var\n"
                                "$my_var = 5\n"
                                "END PROGRAM\n")

    def test_variable_function(self):
        my_var = self.program.create_variable("complex_var")
        my_var.ENABLE(Axis.AB)

        self.desired_content = ("DVAR $complex_var\n"
                                "$complex_var = ENABLE A B\n"
                                "END PROGRAM\n")
