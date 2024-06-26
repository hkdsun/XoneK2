from __future__ import absolute_import, print_function, unicode_literals
from builtins import map, range
from _Framework.MixerComponent import MixerComponent as MixerComponentBase
from .track_filter import TrackFilterComponent

class MixerComponent(MixerComponentBase):

    def __init__(self, num_tracks, *a, **k):
        self._track_filters = [TrackFilterComponent() for _ in range(num_tracks)]
        (super(MixerComponent, self).__init__)(num_tracks, *a, **k)
        list(map(self.register_components, self._track_filters))

    def track_filter(self, index):
        return self._track_filters[index]

    def _reassign_tracks(self):
        super(MixerComponent, self)._reassign_tracks()
        tracks = self.tracks_to_use()
        for index in range(len(self._channel_strips)):
            track_index = self._track_offset + index
            track = tracks[track_index] if len(tracks) > track_index else None
            if len(self._track_filters) > index:
                self._track_filters[index].set_track(track)
