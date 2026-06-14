
from rex.interpreter import RexInterpreter

def test_show():
    r = RexInterpreter()
    out = r.run_source('rex.show("yebo")\nrex.return')
    assert out == ["yebo"]
