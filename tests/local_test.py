import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", ".\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/gerber2.zip', verbose=True)
board.render('./tests/output')
# board.render_pdf('./tests/output', 'top_copper')
# board.render_pdf('./tests/output', 'top_silk', 'yellow')
# board.draw_arc('G03X35251Y104090I3000J-861D01*')
