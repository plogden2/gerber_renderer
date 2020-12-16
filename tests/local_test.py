import json
import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", ".\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/Current Panel.zip', verbose=True)
# board.render('./tests/output', silk=True, drc=True)
board.render_pdf('./tests/output', 'top_copper',
                 'white', scale_compensation=(-0.1954, -0.2032), offset=(7, 7))
board.render_pdf('./tests/output', 'bottom_copper',
                 'white', mirrored=True, scale_compensation=(-0.1954, -0.2015), offset=(7, 507))
board.render_pdf('./tests/output', 'top_mask',
                 'black', mirrored=True, scale_compensation=(-0.1954, -0.2032), offset=(7, 7))
board.render_pdf('./tests/output', 'bottom_mask',
                 'black', scale_compensation=(-0.1954, -0.2032), offset=(7, 7))
