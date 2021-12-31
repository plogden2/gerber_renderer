import json
import importlib.util
spec = importlib.util.spec_from_file_location(
    "Gerber", ".\gerber_renderer\Gerber.py")
Gerber = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Gerber)

board = Gerber.Board('./tests/bga.zip', verbose=True)
# board.render('./tests/output', silk=False, drc=False,
#              board_color='black', copper_color='white')
board.render_copper('./tests/output', board_color='black',
                    copper_color='white')
# board.render_pdf('./tests/output', 'top_copper',
#                  'white', scale_compensation=(-0.1954, -0.2032), offset=(14, 8))
# board.render_pdf('./tests/output', 'bottom_copper',
#                  'white', mirrored=True, scale_compensation=(-0.1954, -0.2032), offset=(14, 8))
# board.render_pdf('./tests/output', 'top_mask',
#                  'black', mirrored=True, scale_compensation=(-0.1954, -0.2032), offset=(12, 8))
# board.render_pdf('./tests/output', 'bottom_mask',
#                  'black', scale_compensation=(-0.1954, -0.2032), offset=(12, 8))
