"""Viewer: a window that shows the games of the bot live and step by step (E106).

The SDK writes the messages of spec/protocol/viewer-v1/ to the viewer program in sbm/bin.
"""

from sbm.viewer.window import ViewerWindow, active_window, open_window

__all__ = ["ViewerWindow", "active_window", "open_window"]
