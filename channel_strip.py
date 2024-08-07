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
from _Framework import Task
from _Framework.Dependency import depends
from _Framework.Util import nop
from _Framework.Control import EncoderControl



import logging
logger = logging.getLogger(__name__)
MAX_ALLOWED_VOLUME = 0.85 # 0db

class ChannelStripComponent(ChannelstripComponentBase):
    volume_control = EncoderControl()

    @depends(show_message=nop)
    def __init__(self, show_message=nop, *a, **k):
        (super(ChannelStripComponent, self).__init__)(*a, **k)
        self._show_message = show_message
        self._reset_volume_task = self._tasks.add(Task.run(self.reset_volume))
        self._reset_volume_task.kill()

    def set_track(self, track):
        super(ChannelStripComponent, self).set_track(track)
        if self._track != None:
            self._on_volume_changed.subject = self._track.mixer_device.volume

    def reset_volume(self):
        # TODO: noop for now (it wasnt so useful)
        return
        # if self._track.mixer_device.volume.value > MAX_ALLOWED_VOLUME:
        #     logger.info("Resetting volume to 0db")
        #     self._show_message("Resetting volume to 0db")
        #     self._track.mixer_device.volume.value = MAX_ALLOWED_VOLUME

    def set_volume_control(self, control):
        if self._volume_control != None:
            self._volume_control.remove_value_listener(self._on_volume_control_touched)

        super(ChannelStripComponent, self).set_volume_control(control)

        if self._volume_control != None:
            self._volume_control.add_value_listener(self._on_volume_control_touched)

    def _on_volume_control_touched(self, value):
        if self._track.name == "Master" or self._track == "Main":
            return
        self.song().view.selected_track = self._track
        logger.info("Volume control touched for track: %s" % self._track.name)

    @subject_slot("value")
    def _on_volume_changed(self):
        # self.song().view.selected_track = self._track

        # if volume is more than 0db, reset it to 0db
        if self._track.mixer_device.volume.value > MAX_ALLOWED_VOLUME and self._reset_volume_task.is_killed:
            self._reset_volume_task.restart()
