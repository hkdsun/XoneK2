from __future__ import absolute_import, print_function, unicode_literals
from builtins import range
import Live
from _Generic.Devices import get_parameter_by_name
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
import _Framework.EncoderElement as EncoderElement
from _Framework.Control import ButtonControl


import logging
logger = logging.getLogger("HK-DEBUG")

class TrackFilterComponent(ControlSurfaceComponent):
    reset_button = ButtonControl()

    def __init__(self):
        ControlSurfaceComponent.__init__(self)
        self._track = None
        self._device = None
        self._freq_control = None
        self._reset_button = None
        self.set_reset_button = self.reset_button.set_control_element

    def disconnect(self):
        if self._freq_control != None:
            self._freq_control.release_parameter()
            self._freq_control = None
        if self._reset_button != None:
            self._reset_button.release_parameter()
            self._reset_button = None
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            self._track = None
        self._device = None

    @reset_button.pressed
    def reset_button_pressed(self, _button):
        if self._device != None:
            for parm in self._device.parameters:
                if parm.name == "Cutoff":
                    parm.value = 63.5
                    break

    def on_enabled_changed(self):
        self.update()

    def set_track(self, track):
        if self._track != None:
            self._track.remove_devices_listener(self._on_devices_changed)
            if self._device != None:
                if self._freq_control != None:
                    self._freq_control.release_parameter()
                if self._reset_button != None:
                    self._reset_button.release_parameter()
        self._track = track
        if self._track != None:
            self._track.add_devices_listener(self._on_devices_changed)
        self._on_devices_changed()

    def set_filter_controls(self, freq, reset_button):
        if self._device != None:
            if self._freq_control != None:
                self._freq_control.release_parameter()
            if self._reset_button != None:
                self._reset_button.release_parameter()
        self._freq_control = freq
        self._reset_button = reset_button
        self.update()

    def update(self):
        super(TrackFilterComponent, self).update()
        if self.is_enabled():
            if self._device != None:
                if self._freq_control != None:
                    self._freq_control.release_parameter()
                if self._reset_button != None:
                    self._reset_button.release_parameter()

                parameter = None
                for parm in self._device.parameters:
                    if parm.name == "Cutoff":
                        parameter = parm
                        break
                if parameter is None:
                  return

                if self._freq_control != None:
                  self._freq_control.connect_to(parameter)
                if self._reset_button != None:
                  self.set_reset_button(self._reset_button)

    def _on_devices_changed(self):
        self._device = None
        if self._track != None:
            for index in range(len(self._track.devices)):
                device = self._track.devices[-1 * (index + 1)]
                if device.name == "Macro Filter+EQ":
                    self._device = device
                    break
        self.update()

