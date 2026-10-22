"""tools/check_move.py: a definition moved to another module passes; a changed one fails."""
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).resolve().parents[1] / "tools" / "check_move.py"
if not path.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)
spec = importlib.util.spec_from_file_location("check_move", path)
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

OLD = {"a": "def f(x):\n    return x + 1\n\nclass C:\n    def m(self):\n        return 2\n",
       "b": "import os\n"}


def test_a_move_between_modules_is_neutral():
    new = {"a": "class C:\n    def m(self):\n        return 2\n",
           "b": "import os\n\ndef f(x):\n    return x + 1\n"}
    assert cm.compare(cm.definitions(OLD), cm.definitions(new)) == []


def test_a_changed_or_lost_definition_is_reported():
    new = {"a": "def f(x):\n    return x + 2\n", "b": "import os\n"}
    assert cm.compare(cm.definitions(OLD), cm.definitions(new)) == [
        ("C", "a", "missing"), ("C.m", "a", "missing"), ("f", "a", "changed")]
    assert cm.compare(cm.definitions(OLD), cm.definitions(new), allow={"a:f", "C", "C.m"}) == []
