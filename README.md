# Launchpad Linux

The macOS Launchpad for a Wayland desktop: a full-screen overlay over your blurred desktop with every app as a big
icon and its name, sorted A to Z, in pages. Built for [Umbriel](https://github.com/noctalia-dev/umbriel) and
[Noctalia](https://github.com/noctalia-dev/noctalia) (wlr-layer-shell, live compositor blur, the shell's colours),
but it only needs a compositor with layer-shell.

- **Keyboard first**: arrows, Enter, Esc, Page Up / Down; **type the first letters of an app to jump to it**.
  The mouse pointer hides the moment you use the keyboard, and hovering only selects after the mouse really moves,
  so a resting pointer never highlights the wrong icon.
- **Mouse**: click an app, click the background to close, wheel or two-finger swipe for the next page.
- **Rearrange like Launchpad**: press an icon and drag it (mouse, or a three finger drag; a long press picks it up too); drop on an icon's edge to put it there, on its
  middle to make a **folder** (rename it by clicking its name); hold at the screen edge to turn the page.
- **Settings** (gear, or Ctrl+,): hide apps from Launchpad, sort A to Z again.
- **Background app with a tray icon**: starts at login, `launchpad-toggle` opens / closes it in milliseconds.
- **Theme**: colours from the active Noctalia palette, font from GTK; falls back to Catppuccin Mocha.

## Install

Needs `python-gobject`, `gtk4`, `gtk4-layer-shell` (Arch: `sudo pacman -S python-gobject gtk4 gtk4-layer-shell`).

    ./install.sh        # command, icon, launcher entry, user service (starts now and at login)

Bind `launchpad-toggle` to a key. For the blurred background add a layer rule to Umbriel's config:

    [[layer_rule]]
    match.namespace = "^launchpad-linux$"
    blur = true
    blur_ignore_alpha = 0.1
    blur_optimized = false

Without it the background is just a dark tint.

## Files

| | |
|---|---|
| `launchpad-linux` | the app (GTK4 + layer-shell + a StatusNotifierItem tray icon written on the session bus) |
| `layout.py` | the layout: hidden apps, order, folders; saved in `~/.config/launchpad-linux/layout.json` |
| `launchpad-toggle` | open / close it through D-Bus (what a keyboard shortcut should run) |
| `test_layout.py` | tests for `layout.py` (`python3 test_layout.py`) |

`launchpad-linux --help` lists the command line (`--background`, `--settings`, `--quit`, `--list`).
