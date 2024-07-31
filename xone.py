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
R_CHANNEL = 14 # Right-side controller
L_CHANNEL = 13 # Left-side controller

NUM_TRACKS = 16
NUM_SCENES = 1

# Layer 1
MIDI_MAPPING = {
    "LAYER1": { # Red layer
        "ENCODERS"        : [0, 1, 2, 3],
        "PUSH_ENCODERS"   : [52, 53, 54, 55],
        "KNOBS1"          : [4, 5, 6, 7],
        "KNOBS2"          : [8, 9, 10, 11],
        "KNOBS3"          : [12, 13, 14, 15],
        "BUTTONS1"        : [48, 49, 50, 51],
        "BUTTONS2"        : [44, 45, 46, 47],
        "BUTTONS3"        : [40, 41, 42, 43],
        "GRID1"           : [36, 37, 38, 39],
        "GRID2"           : [32, 33, 34, 35],
        "GRID3"           : [28, 29, 30, 31],
        "GRID4"           : [24, 25, 26, 27],
        "FADERS"          : [16, 17, 18, 19],
        "ENCODER_LL"      : [20],
        "ENCODER_LR"      : [21],
        "PUSH_ENCODER_LL" : [13],
        "PUSH_ENCODER_LR" : [14],
        "BUTTON_LL"       : [12],  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR"       : [15],
    },
    "LAYER2": { # Amber layer
        "ENCODERS"        : [0x16, 0x17, 0x18, 0x19],
        "PUSH_ENCODERS"   : [0x58, 0x59, 0x5A, 0x5B],
        "KNOBS1"          : [0x1A, 0x1B, 0x1C, 0x1D],
        "KNOBS2"          : [0x1E, 0x1F, 0x20, 0x21],
        "KNOBS3"          : [0x22, 0x23, 0x24, 0x25],
        "BUTTONS1"        : [0x54, 0x55, 0x56, 0x57],
        "BUTTONS2"        : [0x50, 0x51, 0x52, 0x53],
        "BUTTONS3"        : [0x4C, 0x4D, 0x4E, 0x4F],
        "GRID1"           : [0x48, 0x49, 0x4A, 0x4B],
        "GRID2"           : [0x44, 0x45, 0x46, 0x47],
        "GRID3"           : [0x40, 0x41, 0x42, 0x43],
        "GRID4"           : [0x3C, 0x3D, 0x3E, 0x3F],
        "FADERS"          : [0x26, 0x27, 0x28, 0x29],
        "ENCODER_LL"      : [0x2A],
        "ENCODER_LR"      : [0x2B],
        "PUSH_ENCODER_LL" : [0x11],
        "PUSH_ENCODER_LR" : [0x12],
        "BUTTON_LL"       : [0x10],  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR"       : [0x13],
    },
    "LAYER3": { # Green layer
        "ENCODERS"        : [0x2C, 0x2D, 0x2E, 0x2F],
        "PUSH_ENCODERS"   : [0x7C, 0x7D, 0x7E, 0x7F],
        "KNOBS1"          : [0x30, 0x31, 0x32, 0x33],
        "KNOBS2"          : [0x34, 0x35, 0x36, 0x37],
        "KNOBS3"          : [0x38, 0x39, 0x3A, 0x3B],
        "BUTTONS1"        : [0x78, 0x79, 0x7A, 0x7B],
        "BUTTONS2"        : [0x74, 0x75, 0x76, 0x77],
        "BUTTONS3"        : [0x70, 0x71, 0x72, 0x73],
        "GRID1"           : [0x6C, 0x6D, 0x6E, 0x6F],
        "GRID2"           : [0x68, 0x69, 0x6A, 0x6B],
        "GRID3"           : [0x64, 0x65, 0x66, 0x67],
        "GRID4"           : [0x60, 0x61, 0x62, 0x63],
        "FADERS"          : [0x3C, 0x3D, 0x3E, 0x3F],
        "ENCODER_LL"      : [0x44],
        "ENCODER_LR"      : [0x45],
        "PUSH_ENCODER_LL" : [0x15],
        "PUSH_ENCODER_LR" : [0x16],
        "BUTTON_LL"       : [0x14],  # DO NOT USE - RESERVED FOR LATCHING LAYERS
        "BUTTON_LR"       : [0x17],
    }
}

RED_LAYER   = "LAYER1"
AMBER_LAYER = "LAYER2"
GREEN_LAYER = "LAYER3"

def midi_map(controller, layer, control, cc_index=None):
    if controller not in ["L", "R"]:
        raise ValueError("Invalid controller: %s" % controller)
    if layer not in ["LAYER1", "LAYER2", "LAYER3"]:
        raise ValueError("Invalid layer: %s" % layer)
    if control not in MIDI_MAPPING[layer]:
        raise ValueError("Invalid control: %s" % control)
    if cc_index is not None and cc_index >= len(MIDI_MAPPING[layer][control]):
        raise ValueError("Invalid cc_index: %s" % cc_index)

    mapping = MIDI_MAPPING[layer][control]
    if cc_index is not None:
        mapping = [mapping[cc_index]]

    if controller == "L":
        return list(map(lambda x: (mapping[x], L_CHANNEL), range(len(mapping))))
    else:
        return list(map(lambda x: (mapping[x], R_CHANNEL), range(len(mapping))))

def midi_map_all_layers(controller, control, cc_index=None):
    mappings = []
    for layer in [AMBER_LAYER, GREEN_LAYER, RED_LAYER]:
        for cc, channel in midi_map(controller, layer, control, cc_index):
            mappings.append((cc, channel))
    return mappings


# Right-side controls

NEW_TRACK_BUTTON          = midi_map_all_layers("R", "BUTTONS3", cc_index=0)
RECORD_BUTTONS            = midi_map_all_layers("R", "BUTTONS3", cc_index=1)
METRO_BUTTONS             = midi_map_all_layers("R", "BUTTONS3", cc_index=2)
STOP_ALL_CLIPS_BUTTONS    = midi_map_all_layers("R", "BUTTONS3", cc_index=3)
PLAY_BUTTONS              = midi_map_all_layers("R", "BUTTON_LR")
LAYER_SWITCH_BUTTONS      = midi_map_all_layers("R", "BUTTON_LL") # We will spy on this button to switch transport buttons

# Left-side controls
GLOBAL_STOP_BUTTON        = midi_map("L", AMBER_LAYER, "BUTTON_LR")
UNDO_BUTTON               = midi_map("L", AMBER_LAYER, "BUTTONS3", cc_index=0)

# Channel strip controls
FILTER_ENCODERS           = midi_map("R", AMBER_LAYER, "ENCODERS")      + midi_map("L", AMBER_LAYER, "ENCODERS")      + midi_map("R", GREEN_LAYER, "ENCODERS")      + midi_map("R", RED_LAYER, "ENCODERS")
FILTER_RESET_BUTTONS      = midi_map("R", AMBER_LAYER, "PUSH_ENCODERS") + midi_map("L", AMBER_LAYER, "PUSH_ENCODERS") + midi_map("R", GREEN_LAYER, "PUSH_ENCODERS") + midi_map("R", RED_LAYER, "PUSH_ENCODERS")
SENDS_A_KNOBS             = midi_map("R", AMBER_LAYER, "KNOBS1")        + midi_map("L", AMBER_LAYER, "KNOBS1")        + midi_map("R", GREEN_LAYER, "KNOBS1")        + midi_map("R", RED_LAYER, "KNOBS1")
SENDS_B_KNOBS             = midi_map("R", AMBER_LAYER, "KNOBS2")        + midi_map("L", AMBER_LAYER, "KNOBS2")        + midi_map("R", GREEN_LAYER, "KNOBS2")        + midi_map("R", RED_LAYER, "KNOBS2")
VOLUME_FADERS             = midi_map("R", AMBER_LAYER, "FADERS")        + midi_map("L", AMBER_LAYER, "FADERS")        + midi_map("R", GREEN_LAYER, "FADERS")        + midi_map("R", RED_LAYER, "FADERS")
MUTE_BUTTONS              = midi_map("R", AMBER_LAYER, "BUTTONS1")      + midi_map("L", AMBER_LAYER, "BUTTONS1")      + midi_map("R", GREEN_LAYER, "BUTTONS1")      + midi_map("R", RED_LAYER, "BUTTONS1")
LAUNCH_BUTTONS            = midi_map("R", AMBER_LAYER, "GRID1")         + midi_map("L", AMBER_LAYER, "GRID1")         + midi_map("R", GREEN_LAYER, "GRID1")         + midi_map("R", RED_LAYER, "GRID1")
STOP_BUTTONS              = midi_map("R", AMBER_LAYER, "GRID2")         + midi_map("L", AMBER_LAYER, "GRID2")         + midi_map("R", GREEN_LAYER, "GRID2")         + midi_map("R", RED_LAYER, "GRID2")
SOLO_BUTTONS              = midi_map("R", AMBER_LAYER, "GRID3")         + midi_map("L", AMBER_LAYER, "GRID3")         + midi_map("R", GREEN_LAYER, "GRID3")         + midi_map("R", RED_LAYER, "GRID3")
ARM_BUTTONS               = midi_map("R", AMBER_LAYER, "GRID4")         + midi_map("L", AMBER_LAYER, "GRID4")         + midi_map("R", GREEN_LAYER, "GRID4")         + midi_map("R", RED_LAYER, "GRID4")



def button(cc, name=None):
    channel = cc[1]
    cc = cc[0]
    rv = ButtonElement(True, MIDI_NOTE_TYPE, channel, cc)
    if name is not None:
        rv.name = name
    return rv

def fader(cc):
    channel = cc[1]
    cc = cc[0]
    return SliderElement(MIDI_CC_TYPE, channel, cc)

def knob(cc):
    channel = cc[1]
    cc = cc[0]
    return EncoderElement(MIDI_CC_TYPE, channel, cc, Live.MidiMap.MapMode.absolute)

def encoder(cc, map_mode=Live.MidiMap.MapMode.absolute, encoder_sensitivity=1.0):
    channel = cc[1]
    cc = cc[0]
    return EncoderElement(MIDI_CC_TYPE, channel, cc, map_mode, encoder_sensitivity=encoder_sensitivity)


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
            self.init_transport()
            self.init_undo_redo()
            self.init_scene_launch()
            self.init_mixer()
            self.init_layer_switch()

            self.session.set_mixer(self.mixer)
            self.session.update()
            self._set_suppress_rebuild_requests(False)
            log('HK-DEBUG XoneK2 initialized')

    def init_scene_launch(self):
        scene = self.session.scene(0)
        scene.name = 'Scene 0'
        self.session.set_stop_all_clips_button(button(STOP_ALL_CLIPS_BUTTONS[0]))
        self.session.set_stop_track_clip_buttons([button(b) for b in STOP_BUTTONS])


    def init_session(self):
        self.session = SessionComponent(NUM_TRACKS, NUM_SCENES)
        self.session.name = 'Session'

        self.session.update()

    def init_transport(self):
        self.transport = TransportComponent()
        self.transport.set_play_button(button(PLAY_BUTTONS[0]))
        self.transport.set_record_button(button(RECORD_BUTTONS[0]))
        self.transport.set_metronome_button(button(METRO_BUTTONS[0]))
        self.transport.set_stop_button(button(GLOBAL_STOP_BUTTON[0]))
        self.transport.update()

    def init_mixer(self):
        self.mixer = MixerComponent(num_tracks=NUM_TRACKS)
        self.mixer.id = 'Mixer'

        log('HK-DEBUG init_mixer')
        self.mixer.set_volume_controls([fader(VOLUME_FADERS[i]) for i in range(NUM_TRACKS)])
        for i in range(NUM_TRACKS):
            self.mixer.channel_strip(i).set_send_controls([knob(SENDS_A_KNOBS[i]), knob(SENDS_B_KNOBS[i])])
            filter = self.mixer.track_filter(i)
            enc = encoder(FILTER_ENCODERS[i], Live.MidiMap.MapMode.relative_smooth_two_compliment, encoder_sensitivity=5.0)
            enc.mapping_sensitivity = 5.0
            reset_button = button(FILTER_RESET_BUTTONS[i])
            filter.set_filter_controls(enc, reset_button)

        self.mixer.set_solo_buttons([button(SOLO_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_mute_buttons([button(MUTE_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_arm_buttons([button(ARM_BUTTONS[i]) for i in range(NUM_TRACKS)])
        self.mixer.set_new_track_button([button(NEW_TRACK_BUTTON[0])])
        self.mixer.update()

    def init_undo_redo(self):
        def _undo(_):
            if self.song().can_undo:
                self.song().undo()
        def _redo(_):
            if self.song().can_redo:
                self.song().redo()
        undo_button = button(UNDO_BUTTON[0])
        undo_button.add_value_listener(_undo)

    def _on_layer_switch(self, layer, _value):
        layer = (layer + 1) % len(LAYER_SWITCH_BUTTONS) # Cycle through layers
        self.transport.set_play_button(button(PLAY_BUTTONS[layer]))
        self.transport.set_record_button(button(RECORD_BUTTONS[layer]))
        self.transport.set_metronome_button(button(METRO_BUTTONS[layer]))
        self.session.set_stop_all_clips_button(button(STOP_ALL_CLIPS_BUTTONS[layer]))

    def init_layer_switch(self):
        for layer, b in enumerate(LAYER_SWITCH_BUTTONS):
            button(b).add_value_listener(partial(self._on_layer_switch, layer))
