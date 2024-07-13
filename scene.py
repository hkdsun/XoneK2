from __future__ import absolute_import, print_function, unicode_literals
from builtins import map, range
from _Framework.SceneComponent import SceneComponent as SceneComponentBase
import logging

logger = logging.getLogger("XoneK2")

class SceneComponent(SceneComponentBase):


    def update(self):
        super(SceneComponentBase, self).update()
        if self._allow_updates:
            if self._scene != None and self.is_enabled():
                clip_index = self._track_offset # Usually 0
                tracks = self.song().tracks
                tracks_to_use = self._tracks_to_use_callback()
                scene_slots = self._scene.clip_slots
                if self._track_offset > 0:
                    real_offset = 0
                    visible_tracks = 0
                    while visible_tracks < self._track_offset and len(tracks) > real_offset:
                        if tracks[real_offset].is_visible:
                            visible_tracks += 1
                        real_offset += 1
                    clip_index = real_offset
                for track in tracks_to_use:
                    if clip_index >= len(self._clip_slots):
                        break
                    if not track.is_visible:
                        continue
                    track_index = list(tracks).index(track)
                    slot = self._clip_slots[clip_index]
                    if len(scene_slots) > clip_index:
                        slot.set_clip_slot(scene_slots[track_index])
                    else:
                        slot.set_clip_slot(None)
                    clip_index += 1
            else:
                for slot in self._clip_slots:
                    slot.set_clip_slot(None)
            self._update_launch_button()
        else:
            self._update_requests += 1
