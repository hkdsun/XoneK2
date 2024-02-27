from __future__ import with_statement
from functools import partial
import time

import Live
import MidiRemoteScript
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.ClipCreator import ClipCreator
from _Framework.EncoderElement import EncoderElement
from _Framework.InputControlElement import *
from _Framework.SessionComponent import SessionComponent
from _Framework.SessionRecordingComponent import SessionRecordingComponent
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.MixerComponent import MixerComponent


g_logger = None
DEBUG = True


def log(msg):
    global g_logger
    if DEBUG:
        if g_logger is not None:
            g_logger(msg)


EQ_DEVICES = {
    'Eq8': {
        'Gains': ['%i Gain A' % (index + 1) for index in range(8)]
    },
    'FilterEQ3': {
        'Gains': ['GainLo', 'GainMid', 'GainHi'],
        'Cuts': ['LowOn', 'MidOn', 'HighOn']
    }
}

# Channels are counted from 0. This is what people would normally call
# channel 15.
CHANNEL = 14

NUM_TRACKS = 4
NUM_SCENES = 1

# Layer 1
MIDI_MAPPING = {
    "LAYER1": {
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
    "LAYER2": {
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
    "LAYER3": {} # UNIMPLEMENTED
}

USE_LAYER = "LAYER2"

ENCODERS = MIDI_MAPPING[USE_LAYER]["ENCODERS"]
PUSH_ENCODERS = MIDI_MAPPING[USE_LAYER]["PUSH_ENCODERS"]

KNOBS1 = MIDI_MAPPING[USE_LAYER]["KNOBS1"]
KNOBS2 = MIDI_MAPPING[USE_LAYER]["KNOBS2"]
KNOBS3 = MIDI_MAPPING[USE_LAYER]["KNOBS3"]

BUTTONS1 = MIDI_MAPPING[USE_LAYER]["BUTTONS1"]
BUTTONS2 = MIDI_MAPPING[USE_LAYER]["BUTTONS2"]
BUTTONS3 = MIDI_MAPPING[USE_LAYER]["BUTTONS3"]

GRID1 = MIDI_MAPPING[USE_LAYER]["GRID1"]
GRID2 = MIDI_MAPPING[USE_LAYER]["GRID2"]
GRID3 = MIDI_MAPPING[USE_LAYER]["GRID3"]
GRID4 = MIDI_MAPPING[USE_LAYER]["GRID4"]

FADERS = MIDI_MAPPING[USE_LAYER]["FADERS"]

ENCODER_LL = MIDI_MAPPING[USE_LAYER]["ENCODER_LL"]
ENCODER_LR = MIDI_MAPPING[USE_LAYER]["ENCODER_LR"]
PUSH_ENCODER_LL = MIDI_MAPPING[USE_LAYER]["PUSH_ENCODER_LL"]
PUSH_ENCODER_LR = MIDI_MAPPING[USE_LAYER]["PUSH_ENCODER_LR"]

BUTTON_LL = MIDI_MAPPING[USE_LAYER]["BUTTON_LL"]  # DO NOT USE - RESERVED FOR LATCHING LAYERS
BUTTON_LR = MIDI_MAPPING[USE_LAYER]["BUTTON_LR"]

def button(notenr, name=None):
    rv = ButtonElement(True, MIDI_NOTE_TYPE, CHANNEL, notenr)
    if name is not None:
        rv.name = name
    return rv

def fader(notenr):
    return SliderElement(MIDI_CC_TYPE, CHANNEL, notenr)

def knob(cc):
    return EncoderElement(MIDI_CC_TYPE, CHANNEL, cc, Live.MidiMap.MapMode.absolute)

def encoder(cc):
    return EncoderElement(MIDI_CC_TYPE, CHANNEL, cc, Live.MidiMap.MapMode.absolute)


class XoneK2(ControlSurface):
    def __init__(self, c_instance, *a, **k):
        global g_logger
        g_logger = self.log_message
        super(XoneK2, self).__init__(c_instance=c_instance, *a, **k)
        with self.component_guard():
            self._set_suppress_rebuild_requests(True)
            self.init_session()
            self.init_session_recording()
            self.init_transport()
            self.init_undo_redo()
            self.init_scene_launch()
            self.init_mixer()

            self.set_highlighting_session_component(self.session)
            self.session.set_mixer(self.mixer)

            self._set_suppress_rebuild_requests(False)
            log('HK-DEBUG XoneK2 initialized')

    def init_scene_launch(self):
        scene_index = 0
        scene = self.session.scene(scene_index)
        scene.name = 'Scene ' + str(scene_index)
        scene.set_launch_button(button(PUSH_ENCODER_LR))

        self.bind_clip_launch_buttons(scene, scene_index)

        stop_buttons = [button(note_nr) for note_nr in BUTTONS3]
        self.session.set_stop_track_clip_buttons(stop_buttons)


    def init_session(self):
        self.session = SessionComponent(NUM_TRACKS, NUM_SCENES)
        self.session.name = 'Session'

        stop_buttons = [button(note_nr) for note_nr in BUTTONS1]
        self.session.set_stop_track_clip_buttons(stop_buttons)
        self.session.set_stop_all_clips_button(button(GRID4[3]))

        self.bind_session_navigation()
        self.bind_detail_view_toggle()

        self.session.update()

    def init_session_recording(self):
        self.session_recording = SessionRecordingComponent(ClipCreator())
        self.session_recording.set_record_button(button(GRID4[2]))

    def init_transport(self):
        self.transport = TransportComponent()
        self.transport.set_play_button(button(GRID4[0]))
        self.transport.set_stop_button(button(BUTTON_LR))
        self.transport.set_metronome_button(button(GRID3[2]))
        self.transport.set_record_button(button(GRID4[1]))

    def init_mixer(self):
        self.mixer = MixerComponent(num_tracks=NUM_TRACKS)
        self.mixer.id = 'Mixer'

        self.mixer.set_volume_controls([fader(FADERS[i]) for i in range(NUM_TRACKS)])
        for i in range(NUM_TRACKS):
            self.mixer.channel_strip(i).set_send_controls([knob(KNOBS1[i]), knob(KNOBS2[i]), knob(KNOBS3[i])])
        self.mixer.set_solo_buttons([button(BUTTONS1[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_mute_buttons([button(BUTTONS2[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_arm_buttons([button(GRID2[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_track_select_buttons([button(GRID1[i]) for i in range(NUM_TRACKS)])

        self.mixer.update()

    def init_undo_redo(self):
        def _undo(_):
            if self.song().can_undo:
                self.song().undo()
        def _redo(_):
            if self.song().can_redo:
                self.song().redo()
        undo_button = button(GRID3[0])
        redo_button = button(GRID3[1])
        undo_button.add_value_listener(_undo)
        redo_button.add_value_listener(_redo)

    def bind_session_navigation(self):
        def scroll_bank_vertically(value):
            if value == 127:
                self.session._bank_up()
            if value == 1:
                self.session._bank_down()

        enc = encoder(ENCODER_LR)
        enc.add_value_listener(scroll_bank_vertically)

        for i in range(NUM_TRACKS):
            enc = encoder(ENCODERS[i])
            enc.add_value_listener(scroll_bank_vertically)

        def scroll_bank_horizontally(value):
            if value == 127:
                self.session._bank_left()
            if value == 1:
                self.session._bank_right()
        enc = encoder(ENCODER_LL)
        enc.add_value_listener(scroll_bank_horizontally)

    def bind_clip_launch_buttons(self, scene,scene_index):
        for track_index in range(NUM_TRACKS):
            note_nr = PUSH_ENCODERS[track_index]
            b = button(note_nr, name='Clip %d, %d button' % (scene_index, track_index))
            clip_slot = scene.clip_slot(track_index)
            clip_slot.name = 'Clip slot %d, %d' % (scene_index, track_index)
            clip_slot.set_stopped_value(0)
            clip_slot.set_started_value(64)
            clip_slot.set_launch_button(b)

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
                     return

        detail_toggle = button(GRID3[3], name='Detail toggle')
        detail_toggle.add_value_listener(_on_detail_toggle)
