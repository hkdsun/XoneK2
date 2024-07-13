from __future__ import with_statement
from functools import partial
import time

import Live
import MidiRemoteScript
from _Framework.ButtonElement import ButtonElement
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from _Framework.ControlSurface import ControlSurface
from _Framework.ClipCreator import ClipCreator
from _Framework.EncoderElement import EncoderElement
from _Framework.InputControlElement import *
from _Framework.SessionRecordingComponent import SessionRecordingComponent
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from .mixer import MixerComponent
from .session import SessionComponent

g_logger = None
DEBUG = True


def log(msg):
    global g_logger
    if DEBUG:
        if g_logger is not None:
            g_logger(msg)


# Channels are counted from 0. This is what people would normally call
# channel 15.
CHANNEL = 14

NUM_TRACKS = 8
NUM_SCENES = 1

# Layer 1
MIDI_MAPPING = {
    "LAYER1": { # Red layer
        "ENCODERS": [0, 1, 2, 3],
        "PUSH_ENCODERS": [52, 53, 54, 55],
        "KNOBS1": [4, 5, 6, 7],
        "KNOBS2": [8, 9, 10, 11],
        "KNOBS3": [12, 13, 14, 15],
        "BUTTONS1": [48, 49, 50, 51],
        "BUTTONS2": [44, 45, 46, 47],
        "BUTTONS3": [40, 41, 42, 43],
        "GRID1": [36, 37, 38, 39],
        "GRID2": [32, 33, 34, 35],
        "GRID3": [28, 29, 30, 31],
        "GRID4": [24, 25, 26, 27],
        "FADERS": [16, 17, 18, 19],
        "ENCODER_LL": 20,
        "ENCODER_LR": 21,
        "PUSH_ENCODER_LL": 13,
        "PUSH_ENCODER_LR": 14,
        "BUTTON_LL": 12,  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR": 15,
    },
    "LAYER2": { # Amber layer
        "ENCODERS": [0x16, 0x17, 0x18, 0x19],
        "PUSH_ENCODERS": [0x58, 0x59, 0x5A, 0x5B],
        "KNOBS1": [0x1A, 0x1B, 0x1C, 0x1D],
        "KNOBS2": [0x1E, 0x1F, 0x20, 0x21],
        "KNOBS3": [0x22, 0x23, 0x24, 0x25],
        "BUTTONS1": [0x54, 0x55, 0x56, 0x57],
        "BUTTONS2": [0x50, 0x51, 0x52, 0x53],
        "BUTTONS3": [0x4C, 0x4D, 0x4E, 0x4F],
        "GRID1": [0x48, 0x49, 0x4A, 0x4B],
        "GRID2": [0x44, 0x45, 0x46, 0x47],
        "GRID3": [0x40, 0x41, 0x42, 0x43],
        "GRID4": [0x3C, 0x3D, 0x3E, 0x3F],
        "FADERS": [0x26, 0x27, 0x28, 0x29],
        "ENCODER_LL": 0x2A,
        "ENCODER_LR": 0x2B,
        "PUSH_ENCODER_LL": 0x11,
        "PUSH_ENCODER_LR": 0x12,
        "BUTTON_LL": 0x10,  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR": 0x13,
    },
    "LAYER3": { # Green layer
        "ENCODERS": [0x2C, 0x2D, 0x2E, 0x2F],
        "PUSH_ENCODERS": [0x7C, 0x7D, 0x7E, 0x7F],
        "KNOBS1": [0x30, 0x31, 0x32, 0x33],
        "KNOBS2": [0x34, 0x35, 0x36, 0x37],
        "KNOBS3": [0x38, 0x39, 0x3A, 0x3B],
        "BUTTONS1": [0x78, 0x79, 0x7A, 0x7B],
        "BUTTONS2": [0x74, 0x75, 0x76, 0x77],
        "BUTTONS3": [0x70, 0x71, 0x72, 0x73],
        "GRID1": [0x6C, 0x6D, 0x6E, 0x6F],
        "GRID2": [0x68, 0x69, 0x6A, 0x6B],
        "GRID3": [0x64, 0x65, 0x66, 0x67],
        "GRID4": [0x60, 0x61, 0x62, 0x63],
        "FADERS": [0x3C, 0x3D, 0x3E, 0x3F],
        "ENCODER_LL": 0x44,
        "ENCODER_LR": 0x45,
        "PUSH_ENCODER_LL": 0x15,
        "PUSH_ENCODER_LR": 0x16,
        "BUTTON_LL": 0x14,  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR": 0x17,
    }
}

DEFAULT_LAYER = "LAYER2"
SECONDARY_LAYER = "LAYER3"

ENCODERS = MIDI_MAPPING[DEFAULT_LAYER]["ENCODERS"] + MIDI_MAPPING[SECONDARY_LAYER]["ENCODERS"]
PUSH_ENCODERS = MIDI_MAPPING[DEFAULT_LAYER]["PUSH_ENCODERS"] + MIDI_MAPPING[SECONDARY_LAYER]["PUSH_ENCODERS"]

# User assignable buttons
USER_ASSIGNABLE_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["BUTTONS2"] + MIDI_MAPPING[SECONDARY_LAYER]["BUTTONS2"]
USER_ASSIGNABLE_KNOBS = MIDI_MAPPING[DEFAULT_LAYER]["KNOBS3"] + MIDI_MAPPING[SECONDARY_LAYER]["KNOBS3"]

# DAW Transport buttons
TRANSPORT_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["BUTTONS3"] + MIDI_MAPPING[SECONDARY_LAYER]["BUTTONS3"]

# Track controls
SENDS_A_KNOBS = MIDI_MAPPING[DEFAULT_LAYER]["KNOBS1"] + MIDI_MAPPING[SECONDARY_LAYER]["KNOBS1"]
SENDS_B_KNOBS = MIDI_MAPPING[DEFAULT_LAYER]["KNOBS2"] + MIDI_MAPPING[SECONDARY_LAYER]["KNOBS2"]
VOLUME_FADERS = MIDI_MAPPING[DEFAULT_LAYER]["FADERS"] + MIDI_MAPPING[SECONDARY_LAYER]["FADERS"]

MUTE_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["BUTTONS1"] + MIDI_MAPPING[SECONDARY_LAYER]["BUTTONS1"]
LAUNCH_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["GRID1"] + MIDI_MAPPING[SECONDARY_LAYER]["GRID1"]
STOP_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["GRID2"] + MIDI_MAPPING[SECONDARY_LAYER]["GRID2"]
SOLO_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["GRID3"] + MIDI_MAPPING[SECONDARY_LAYER]["GRID3"]
ARM_BUTTONS = MIDI_MAPPING[DEFAULT_LAYER]["GRID4"] + MIDI_MAPPING[SECONDARY_LAYER]["GRID4"]

ENCODER_LL = MIDI_MAPPING[DEFAULT_LAYER]["ENCODER_LL"]
ENCODER_LR = MIDI_MAPPING[DEFAULT_LAYER]["ENCODER_LR"]
S_ENCODER_LL = MIDI_MAPPING[SECONDARY_LAYER]["ENCODER_LL"]
S_ENCODER_LR = MIDI_MAPPING[SECONDARY_LAYER]["ENCODER_LR"]

PUSH_ENCODER_LL = MIDI_MAPPING[DEFAULT_LAYER]["PUSH_ENCODER_LL"]
PUSH_ENCODER_LR = MIDI_MAPPING[DEFAULT_LAYER]["PUSH_ENCODER_LR"]
S_PUSH_ENCODER_LL = MIDI_MAPPING[SECONDARY_LAYER]["PUSH_ENCODER_LL"]
S_PUSH_ENCODER_LR = MIDI_MAPPING[SECONDARY_LAYER]["PUSH_ENCODER_LR"]

BUTTON_LL = MIDI_MAPPING[DEFAULT_LAYER]["BUTTON_LL"]  # DO NOT USE - RESERVED FOR LATCHING LAYERS
BUTTON_LR = MIDI_MAPPING[DEFAULT_LAYER]["BUTTON_LR"]
S_BUTTON_LR = MIDI_MAPPING[SECONDARY_LAYER]["BUTTON_LR"]


def button(notenr, name=None):
    rv = ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, notenr)
    if name is not None:
        rv.name = name
    return rv

def fader(notenr):
    return SliderElement(MIDI_CC_TYPE, CHANNEL, notenr)

def knob(cc):
    return EncoderElement(MIDI_CC_TYPE, CHANNEL, cc, Live.MidiMap.MapMode.absolute)

def encoder(cc, map_mode=Live.MidiMap.MapMode.absolute, encoder_sensitivity=1.0):
    return EncoderElement(MIDI_CC_TYPE, CHANNEL, cc, map_mode, encoder_sensitivity=encoder_sensitivity)


class HighPassEncoder:
    def __init__(self, cc):
        self.encoder = encoder(cc)
        self.last_scroll_time = 0
        self.last_value = None
        self.encoder.add_value_listener(self._on_value)

    def add_value_listener(self, callback):
        self._callback = callback

    def _on_value(self, value):
        if self._callback is None:
            return
        self._callback(value)
class XoneK2(ControlSurface):
    def __init__(self, c_instance, *a, **k):
        global g_logger
        g_logger = self.log_message
        super(XoneK2, self).__init__(c_instance=c_instance, *a, **k)
        with self.component_guard():
            self._set_suppress_rebuild_requests(True)
            self.init_session()
            # self.init_session_recording()
            self.init_transport()
            self.init_undo_redo()
            self.init_scene_launch()
            self.init_mixer()

            self.set_highlighting_session_component(self.session)
            self.session.set_mixer(self.mixer)
            self.session.update()
            self._set_suppress_rebuild_requests(False)
            log('HK-DEBUG XoneK2 initialized')

    def init_scene_launch(self):
        scene = self.session.scene(0)
        scene.name = 'Scene 0'

        def _new(value):
            if value != 127:
                return
            self.song().create_scene(self.session.scene_offset() + 1)
        def _select(value):
            if value != 127:
                return
            scene._do_select_scene(None)
        def _delete(value):
            if value != 127:
                return
            scene._do_select_scene(None)
            scene._do_delete_scene(None)
        def _duplicate(value):
            if value != 127:
                return
            self.song().duplicate_scene(self.session.scene_offset())

        # Scene launch button
        # scene.set_launch_button(button(S_BUTTON_LR))

        # Bind new, select, delete, and duplicate scene buttons
        # button(GRID6[0]).add_value_listener(_new)
        # button(GRID6[1]).add_value_listener(_delete)
        # button(GRID6[2]).add_value_listener(_duplicate)
        self.session.set_stop_all_clips_button(button(TRANSPORT_BUTTONS[3]))

        # Bind all the encoders to select the scene
        button(PUSH_ENCODER_LR).add_value_listener(partial(_select))
        button(PUSH_ENCODER_LL).add_value_listener(partial(_select))
        button(S_PUSH_ENCODER_LR).add_value_listener(partial(_select))
        button(S_PUSH_ENCODER_LL).add_value_listener(partial(_select))

        button_matrix = ButtonMatrixElement(rows=[[button(b) for b in LAUNCH_BUTTONS]], name="clip launch buttons")
        self.session.set_clip_launch_buttons(button_matrix)
        self.session.set_stop_track_clip_buttons([button(b) for b in STOP_BUTTONS])


    def init_session(self):
        self.session = SessionComponent(NUM_TRACKS, NUM_SCENES)
        self.session.name = 'Session'

        self.bind_session_navigation()
        self.bind_detail_view_toggle()
        self.session.update()
        # self.bind_session_view_toggle()
        # self.bind_browser_view_toggle()

    # def init_session_recording(self):
    #     self.session_recording = SessionRecordingComponent(ClipCreator())
        # self.session_recording.set_record_button(button(TRANSPORT_BUTTONS[2]))

    def init_transport(self):
        self.transport = TransportComponent()
        self.transport.set_play_button(button(TRANSPORT_BUTTONS[0]))
        self.transport.set_stop_button(button(BUTTON_LR))
        self.transport.set_metronome_button(button(TRANSPORT_BUTTONS[2]))
        self.transport.set_record_button(button(TRANSPORT_BUTTONS[1]))
        self.transport.update()

    def init_mixer(self):
        self.mixer = MixerComponent(num_tracks=NUM_TRACKS)
        self.mixer.id = 'Mixer'

        log('HK-DEBUG init_mixer')
        self.mixer.set_volume_controls([fader(VOLUME_FADERS[i]) for i in range(NUM_TRACKS)])
        for i in range(NUM_TRACKS):
            self.mixer.channel_strip(i).set_send_controls([knob(SENDS_A_KNOBS[i]), knob(SENDS_B_KNOBS[i])])
            filter = self.mixer.track_filter(i)
            enc = encoder(ENCODERS[i], Live.MidiMap.MapMode.relative_smooth_two_compliment, encoder_sensitivity=5.0)
            enc.mapping_sensitivity = 5.0
            reset_button = button(PUSH_ENCODERS[i])
            filter.set_filter_controls(enc, reset_button)

        self.mixer.set_solo_buttons([button(SOLO_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_mute_buttons([button(MUTE_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_arm_buttons([button(ARM_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_new_track_button(button(TRANSPORT_BUTTONS[5]))
        self.mixer.update()

    def init_undo_redo(self):
        def _undo(_):
            if self.song().can_undo:
                self.song().undo()
        def _redo(_):
            if self.song().can_redo:
                self.song().redo()
        undo_button = button(TRANSPORT_BUTTONS[4])
        # redo_button = button(TRANSPORT_BUTTONS[5])
        undo_button.add_value_listener(_undo)
        # redo_button.add_value_listener(_redo)

    def bind_session_navigation(self):
        def scroll_bank_vertically(value):
            if value == 127:
                self.session._bank_up()
            if value == 1:
                self.session._bank_down()
        def scroll_bank_horizontally(value):
            if value == 127:
                self.session._bank_left()
            if value == 1:
                self.session._bank_right()


        # enc = HighPassEncoder(ENCODER_LL)
        # enc.add_value_listener(scroll_bank_horizontally)
        enc = HighPassEncoder(ENCODER_LR)
        enc.add_value_listener(scroll_bank_vertically)
        enc = HighPassEncoder(S_ENCODER_LR)
        enc.add_value_listener(scroll_bank_vertically)
        enc = HighPassEncoder(ENCODER_LL)
        enc.add_value_listener(scroll_bank_vertically)
        enc = HighPassEncoder(S_ENCODER_LL)
        enc.add_value_listener(scroll_bank_vertically)

    def bind_detail_view_toggle(self):
        def _on_detail_toggle(value):
            if not value == 127:
                return

            if not self.application().view.is_view_visible('Detail'):
                self.application().view.show_view('Detail/Clip')
            else:
                if self.application().view.is_view_visible('Detail/Clip'):
                    self.application().view.show_view('Detail/DeviceChain')
                    return
                if self.application().view.is_view_visible('Detail/DeviceChain'):
                     self.application().view.hide_view('Detail')
                     self.application().view.hide_view('Browser')
                     return

        detail_toggle = button(TRANSPORT_BUTTONS[7], name='Detail toggle')
        detail_toggle.add_value_listener(_on_detail_toggle)

    def bind_session_view_toggle(self):
        def _on_session_toggle(value):
            if not value == 127:
                return

            if not self.application().view.is_view_visible('Session'):
                self.application().view.show_view('Session')
            else:
                self.application().view.hide_view('Session')

        session_toggle = button(TRANSPORT_BUTTONS[9999], name='Session toggle')
        session_toggle.add_value_listener(_on_session_toggle)

    def bind_browser_view_toggle(self):
        def _on_browser_toggle(value):
            if not value == 127:
                return

            if not self.application().view.is_view_visible('Browser'):
                self.application().view.show_view('Browser')
            else:
                self.application().view.hide_view('Browser')

        browser_toggle = button(TRANSPORT_BUTTONS[9999], name='Browser toggle')
        browser_toggle.add_value_listener(_on_browser_toggle)
