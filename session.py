from __future__ import absolute_import, print_function, unicode_literals
from builtins import map, range
from _Framework.SessionComponent import SessionComponent as SessionComponentBase
import logging
from .scene import SceneComponent as CustomSceneComponent

logger = logging.getLogger("XoneK2")

class SessionComponent(SessionComponentBase):
  clip_launch_buttons = []
  scene_component_type = CustomSceneComponent

  def set_clip_launch_buttons(self, buttons):
      if buttons:
          for button, (x, y) in buttons.iterbuttons():
              scene = self.scene(y)
              slot = scene.clip_slot(x)
              slot.set_launch_button(button)

