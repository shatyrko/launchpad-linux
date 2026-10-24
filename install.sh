#!/usr/bin/env bash
# Install Launchpad Linux for the current user: the command, the icon, the launcher entry and the background
# service (starts at login, shows a tray icon). Safe to run again.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bin="$HOME/.local/bin"
mkdir -p "$bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps" "$HOME/.config/systemd/user"
ln -sf "$here/launchpad-linux" "$bin/launchpad-linux"
ln -sf "$here/launchpad-toggle" "$bin/launchpad-toggle"
install -m644 "$here/data/dev.alecsh.LaunchpadLinux.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/"
install -m644 "$here/data/dev.alecsh.LaunchpadLinux.desktop" "$HOME/.local/share/applications/"
install -m644 "$here/data/launchpad-linux.service" "$HOME/.config/systemd/user/"
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now launchpad-linux.service
systemctl --user restart launchpad-linux.service
echo "Launchpad Linux installed: run 'launchpad-toggle' (instant) or 'launchpad-linux' (it toggles), tray icon id 'launchpad-linux'."
