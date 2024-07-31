from __future__ import absolute_import, print_function, unicode_literals
from builtins import range
import Live
from _Generic.Devices import get_parameter_by_name
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
import _Framework.EncoderElement as EncoderElement
from _Framework.Control import ButtonControl
from _Framework.SubjectSlot import subject_slot_group
from ableton.v3.live import liveobj_valid

import logging
logger = logging.getLogger("HK-DEBUG")

class TrackFilterComponent(ControlSurfaceComponent):

    def __init__(self):
        ControlSurfaceComponent.__init__(self)
        self._track = None
        self._device = None
        self._freq_control = None
        self._reset_button = None

    def disconnect(self):
        if self._freq_control != None:
            self._freq_control.release_parameter()
            self._freq_control = None
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            self._track = None
        self._device = None

    def reset_button_handler(self, value):
        if value == 127:
            if self._track != None and liveobj_valid(self._track):
                self.song().view.selected_track = self._track

            for send in self._track.mixer_device.sends:
                send.value = 0

            if self._device != None:
                for param in self._device.parameters[1:]:
                    if param.state in [0, 1]:
                        param.value = param.default_value

            self._reset_button.turn_off()

    def on_enabled_changed(self):
        self.update()

    def set_track(self, track):
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            if self._device != None:
                if self._freq_control != None:
                    self._freq_control.release_parameter()
        self._track = track
        if self._track != None:
            self._track.add_devices_listener(self._on_devices_changed)
        self._on_devices_changed()

    @subject_slot_group("value")
    def __on_parameter_value_changed(self, parameter):
        if parameter.value != parameter.default_value:
            self._reset_button.turn_on()

    def set_filter_controls(self, freq, reset_button):
        if self._device != None:
            if self._freq_control != None:
                self._freq_control.release_parameter()
        self._freq_control = freq
        self._reset_button = reset_button
        self._reset_button.add_value_listener(self.reset_button_handler)

        self.update()

    def update(self):
        super(TrackFilterComponent, self).update()
        if self.is_enabled():
            if self._device != None:
                if self._freq_control != None:
                    self._freq_control.release_parameter()

                parameter = None
                for parm in self._device.parameters:
                    if parm.name == "Lowpass":
                        parameter = parm
                        break
                if parameter is None:
                    return

                if self._freq_control != None:
                    self._freq_control.connect_to(parameter)


    def _on_devices_changed(self):
        self._device = None
        if self._track != None:
            for index in range(len(self._track.devices)):
                device = self._track.devices[-1 * (index + 1)]
                if device.name == "Macro Filter+EQ":
                    self._device = device
                    self._TrackFilterComponent__on_parameter_value_changed.replace_subjects(self._device.parameters)
                    break
        self.update()

