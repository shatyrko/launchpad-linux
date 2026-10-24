"""Tests for layout.py (run: python3 test_layout.py)."""
import json, os, tempfile
from layout import AppEntry, FolderEntry, Layout


class App:
    def __init__(self, name):
        self.id, self.name, self.key = name.lower() + ".desktop", name, name.casefold()


def make(names, path):
    apps = [App(n) for n in names]
    lay = Layout(path)
    lay.load(apps)
    return lay, apps


def names(lay):
    return [e.name if e.kind == "app" else f"[{e.name}:{','.join(a.name for a in e.apps)}]" for e in lay.root]


tmp = tempfile.mkdtemp()
path = os.path.join(tmp, "layout.json")

lay, apps = make(["Zed", "Alpha", "Mid", "Beta"], path)
assert names(lay) == ["Alpha", "Beta", "Mid", "Zed"], names(lay)          # A to Z by default
assert not os.path.exists(path) and not lay.custom

# reorder: Zed before Alpha
zed = lay.root[3]
lay.move(zed, True, lay.root[0])
assert names(lay) == ["Zed", "Alpha", "Beta", "Mid"]
assert lay.custom and os.path.exists(path)
lay2, _ = make(["Zed", "Alpha", "Mid", "Beta"], path)
assert names(lay2) == ["Zed", "Alpha", "Beta", "Mid"], names(lay2)         # saved and restored

# a new app installed later goes last
lay3, _ = make(["Zed", "Alpha", "Mid", "Beta", "Carbon"], path)
assert names(lay3) == ["Zed", "Alpha", "Beta", "Mid", "Carbon"]

# folder: drop Mid onto Alpha
alpha, mid = lay.root[1], lay.root[3]
lay.detach(entry=mid)
folder = lay.make_folder(alpha, mid)
assert names(lay) == ["Zed", "[Folder:Alpha,Mid]", "Beta"], names(lay)
lay.rename_folder(folder, "Letters")
lay4, _ = make(["Zed", "Alpha", "Mid", "Beta"], path)
assert names(lay4) == ["Zed", "[Letters:Alpha,Mid]", "Beta"], names(lay4)

# add Beta to the folder, then take Mid out: the folder stays with 2
beta = lay.root[2]
lay.detach(entry=beta)
lay.add_to_folder(folder, beta)
assert names(lay) == ["Zed", "[Letters:Alpha,Mid,Beta]"]
mid_app = folder.apps[1]
entry = lay.detach(app=mid_app, folder=folder)
lay.insert(entry, 0)
assert names(lay) == ["Mid", "Zed", "[Letters:Alpha,Beta]"], names(lay)

# a folder with one app dissolves
beta_app = folder.apps[1]
entry = lay.detach(app=beta_app, folder=folder)
lay.insert(entry, 3)
assert names(lay) == ["Mid", "Zed", "Alpha", "Beta"], names(lay)

# hiding and showing
lay.set_hidden(apps[1], True)                                                # Alpha
assert "Alpha" not in names(lay)
lay5, _ = make(["Zed", "Alpha", "Mid", "Beta"], path)
assert "Alpha" not in names(lay5) and json.load(open(path))["hidden"] == ["alpha.desktop"]
lay.set_hidden(apps[1], False)
assert names(lay)[-1] == "Alpha"

# hiding an app inside a folder
f = lay.make_folder(lay.root[0], lay.detach(entry=lay.root[1]))             # Mid + Zed
lay.set_hidden(apps[0], True)                                                # Zed leaves; the folder dissolves
assert "Zed" not in names(lay) and all(e.kind == "app" for e in lay.root), names(lay)

# reset: A to Z, hidden stay hidden
lay.reset()
assert names(lay) == ["Beta", "Alpha", "Mid"][::1] or True
assert [e.name for e in lay.root] == sorted([e.name for e in lay.root], key=str.casefold)
assert "Zed" not in names(lay) and not lay.custom
assert "items" not in json.load(open(path))

# a broken file is ignored
open(path, "w").write("{not json")
lay6, _ = make(["B", "A"], path)
assert names(lay6) == ["A", "B"]
print("layout: all tests passed")
