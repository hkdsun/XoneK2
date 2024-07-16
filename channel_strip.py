# uncompyle6 version 3.9.1
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.12.2 (main, Feb  6 2024, 20:19:44) [Clang 15.0.0 (clang-1500.1.0.2.5)]
# Embedded file name: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/Launchpad_MK2/ChannelStripComponent.py
# Compiled at: 2024-03-09 01:30:22
# Size of source mod 2**32: 7016 bytes
from __future__ import absolute_import, print_function, unicode_literals
from itertools import chain
from _Framework.ChannelStripComponent import ChannelStripComponent as ChannelstripComponentBase
from _Framework.SubjectSlot import subject_slot

class ChannelStripComponent(ChannelstripComponentBase):
    def __init__(self, *a, **k):
        (super(ChannelStripComponent, self).__init__)(*a, **k)

    def set_track(self, track):
        super(ChannelStripComponent, self).set_track(track)
        if self._track != None:
            self._on_volume_changed.subject = self._track.mixer_device.volume

    @subject_slot("value")
    def _on_volume_changed(self):
        self.song().view.selected_track = self._track
