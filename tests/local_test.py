import json
import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", ".\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/pp.zip', verbose=True)
board.render('./tests/output', silk=True)
# board.render_pdf('./tests/output', 'top_copper',
#                  'white', scale_compensation=(-0.1961, -0.205), offset=(10, 250))
# board.render_pdf('./tests/output', 'bottom_copper',
#                  'white', mirrored=True, scale_compensation=(-0.1961, -0.205), offset=(10, 250))
# board.render_pdf('./tests/output', 'top_mask',
#                  'black', mirrored=True, scale_compensation=(-0.1961, -0.2018), offset=(10, 10))
# board.render_pdf('./tests/output', 'bottom_mask',
#                  'black', scale_compensation=(-0.1961, -0.2018), offset=(10, 300))
