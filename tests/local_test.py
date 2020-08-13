import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", "D:\Programming\Python\gerber_renderer\gerber_renderer\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/gerber.zip', verbose=True)
board.render('./tests/output')
