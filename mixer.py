from __future__ import absolute_import, print_function, unicode_literals
from builtins import map, range
from _Framework.MixerComponent import MixerComponent as MixerComponentBase
from .track_filter import TrackFilterComponent
from _Framework.Control import ButtonControl
from ableton.v2.base import liveobj_valid

import logging

logger = logging.getLogger("XoneK2")

class MixerComponent(MixerComponentBase):
    new_track_button = ButtonControl()

    STATIC_TRACKS = {
        'Maschine': {},
        'Instruments': {},
        'Loopers': {},
        'MIDI Recorder': {},
    }

    def __init__(self, num_tracks, *a, **k):
        self._track_filters = [TrackFilterComponent() for _ in range(num_tracks)]
        (super(MixerComponent, self).__init__)(num_tracks, *a, **k)
        list(map(self.register_components, self._track_filters))
        self.set_new_track_button = self.new_track_button.set_control_element

    def track_filter(self, index):
        return self._track_filters[index]

    @new_track_button.pressed
    def new_track_button_pressed(self, _button):
        track = self.song().create_audio_track()
        logger.info('New track created: %s', track.name)

        if not track.can_be_armed:
            return

        for i in range(len(track.available_input_routing_types)):
            if track.available_input_routing_types[i].display_name == 'Instruments':
                track.input_routing_type = track.available_input_routing_types[i]
                break

        track.arm = True

        all_tracks = self.tracks(self.song())
        except_midi_and_new_track = filter(lambda t: t != track and t.name != 'MIDI Sender', all_tracks)
        self.unarm_tracks(except_midi_and_new_track)


    def _reassign_tracks(self):
        super(MixerComponent, self)._reassign_tracks()
        tracks = self.tracks_to_use()
        for index in range(len(self._channel_strips)):
            track_index = self._track_offset + index
            track = tracks[track_index] if len(tracks) > track_index else None
            if len(self._track_filters) > index:
                self._track_filters[index].set_track(track)

    def is_static_track(self, track):
        def match(pattern):
            if track.name == pattern:
                return True
            if pattern.startswith('/') and pattern.endswith('/'):
                pattern = pattern[2:-2]
                return pattern in track.name
            else:
                return False

        return any(map(lambda pattern: match(pattern), self.STATIC_TRACKS.keys()))

    def tracks_to_use(self):
        static_tracks = []
        dynamic_tracks = []

        for track in super(MixerComponent, self).tracks_to_use():
            if self.is_static_track(track):
                # logger.info('Static track: %s', track.name)
                static_tracks.insert(0, track)
            else:
                dynamic_tracks.append(track)

        return static_tracks + dynamic_tracks

    def toggle_fold(self, track):
        if is_group_track(track):
            track.fold_state = not track.fold_state
            return True
        return False


    def can_be_armed(self, track):
        if liveobj_valid(track):
            return track.can_be_armed


    def arm(self, track):
        if self.can_be_armed(track):
            track.arm = True
            return True
        return False


    def unarm(self, track):
        if self.can_be_armed(track):
            track.arm = False
            return True
        return False


    def unarm_tracks(self, tracks):
        for track in tracks:
            self.unarm(track)

    def tracks(self, song):
        return filter(liveobj_valid, song.tracks)


    def visible_tracks(self, song):
        return filter(liveobj_valid, song.visible_tracks)
