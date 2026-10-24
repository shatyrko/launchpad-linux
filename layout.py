"""The layout of Launchpad Linux: which apps are hidden, the order of apps and folders.

Pure Python (no GTK) so it can be tested alone. Saved as ~/.config/launchpad-linux/layout.json:

    {"version": 1,
     "hidden": ["org.gnome.Boxes.desktop"],
     "items": ["firefox.desktop", {"folder": "Games", "apps": ["steam.desktop", "other.desktop"]}, ...]}

Without "items" the apps are sorted A to Z. Apps that are not in "items" (installed later) come last,
A to Z. Hidden apps are not in the layout at all; showing one again puts it at the end.
"""
import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/launchpad-linux")
LAYOUT_FILE = os.path.join(CONFIG_DIR, "layout.json")
DEFAULT_FOLDER_NAME = "Folder"


class AppEntry:
    kind = "app"

    def __init__(self, app):
        self.app = app

    @property
    def name(self):
        return self.app.name

    @property
    def key(self):
        return self.app.key


class FolderEntry:
    kind = "folder"

    def __init__(self, name, apps, hidden=False):
        self.name = name or DEFAULT_FOLDER_NAME
        self.apps = list(apps)
        self.hidden = hidden          # kept (with its apps) but not shown

    @property
    def key(self):
        return self.name.casefold()


class Layout:
    def __init__(self, path=LAYOUT_FILE):
        self.path = path
        self.hidden = set()
        self.root = []            # AppEntry / FolderEntry, in order
        self.custom = False       # False = plain A to Z
        self.all_apps = []

    # -- loading and saving ---------------------------------------------------------------------------------------

    def load(self, all_apps):
        self.all_apps = list(all_apps)
        by_id = {a.id: a for a in self.all_apps}
        data = {}
        try:
            with open(self.path) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {}
        self.hidden = {i for i in data.get("hidden", []) if isinstance(i, str)}
        items = data.get("items") if isinstance(data.get("items"), list) else None
        self.custom = items is not None
        placed = set(self.hidden)
        self.root = []
        for item in items or []:
            if isinstance(item, str):
                app = by_id.get(item)
                if app is not None and item not in placed:
                    self.root.append(AppEntry(app))
                    placed.add(item)
            elif isinstance(item, dict) and "folder" in item:
                apps = []
                for ident in item.get("apps", []):
                    app = by_id.get(ident)
                    if app is not None and ident not in placed:
                        apps.append(app)
                        placed.add(ident)
                if apps:
                    self.root.append(FolderEntry(str(item.get("folder") or DEFAULT_FOLDER_NAME), apps, bool(item.get("hidden"))))
        rest = sorted((a for a in self.all_apps if a.id not in placed), key=lambda a: a.key)
        self.root += [AppEntry(a) for a in rest]
        self.cleanup()

    def to_json(self):
        items = []
        for entry in self.root:
            if entry.kind == "app":
                items.append(entry.app.id)
            else:
                folder = {"folder": entry.name, "apps": [a.id for a in entry.apps]}
                if entry.hidden:
                    folder["hidden"] = True
                items.append(folder)
        data = {"version": 1, "hidden": sorted(self.hidden)}
        if self.custom:
            data["items"] = items
        return data

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.to_json(), f, indent=1, ensure_ascii=False)
        os.replace(tmp, self.path)

    def shown(self):
        """The entries to draw: everything except hidden folders."""
        return [e for e in self.root if not (e.kind == "folder" and e.hidden)]

    def folders(self):
        return [e for e in self.root if e.kind == "folder"]

    def set_folder_hidden(self, folder, hidden):
        folder.hidden = hidden
        self._touch()

    # -- queries -------------------------------------------------------------------------------------------------------

    def find_app(self, app):
        """(root index, folder or None) of an app."""
        for i, entry in enumerate(self.root):
            if entry.kind == "app" and entry.app is app:
                return i, None
            if entry.kind == "folder" and app in entry.apps:
                return i, entry
        return None, None

    # -- changes ---------------------------------------------------------------------------------------------------------

    def cleanup(self):
        """A folder with one app dissolves into that app; an empty one disappears."""
        out = []
        for entry in self.root:
            if entry.kind == "folder" and len(entry.apps) <= 1:
                out += [AppEntry(a) for a in entry.apps]
            else:
                out.append(entry)
        self.root = out

    def _touch(self):
        self.custom = True
        self.cleanup()
        self.save()

    def detach(self, entry=None, app=None, folder=None):
        """Take an entry out of the root (or an app out of a folder); returns the entry to place elsewhere."""
        if folder is not None:
            folder.apps.remove(app)
            return AppEntry(app)
        self.root.remove(entry)
        return entry

    def insert(self, entry, index):
        index = max(0, min(len(self.root), index))
        self.root.insert(index, entry)
        self._touch()

    def move(self, entry, before, target=None):
        """Put an entry (from the root) next to target: before it or after it."""
        self.root.remove(entry)
        index = self.root.index(target) + (0 if before else 1) if target is not None else len(self.root)
        self.root.insert(index, entry)
        self._touch()

    def make_folder(self, target, dragged, name=DEFAULT_FOLDER_NAME):
        """target (an app in the root) and dragged (an app entry, detached) become one folder."""
        index = self.root.index(target)
        folder = FolderEntry(name, [target.app, dragged.app])
        self.root[index] = folder
        self._touch()
        return folder

    def add_to_folder(self, folder, dragged):
        folder.apps.append(dragged.app)
        self._touch()

    def rename_folder(self, folder, name):
        name = name.strip() or DEFAULT_FOLDER_NAME
        if name != folder.name:
            folder.name = name
            self._touch()

    def reorder_in_folder(self, folder, app, before, target=None):
        folder.apps.remove(app)
        index = folder.apps.index(target) + (0 if before else 1) if target is not None else len(folder.apps)
        folder.apps.insert(index, app)
        self._touch()

    def set_hidden(self, app, hidden):
        if hidden:
            self.hidden.add(app.id)
            i, folder = self.find_app(app)
            if i is not None:
                if folder is not None:
                    folder.apps.remove(app)
                else:
                    del self.root[i]
        else:
            self.hidden.discard(app.id)
            if self.find_app(app)[0] is None:
                self.root.append(AppEntry(app))
        self.cleanup()
        self.save()

    def reset(self):
        """Back to A to Z, no folders (hidden apps stay hidden)."""
        self.custom = False
        apps = sorted((a for a in self.all_apps if a.id not in self.hidden), key=lambda a: a.key)
        self.root = [AppEntry(a) for a in apps]
        self.save()
