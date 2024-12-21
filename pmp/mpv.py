"""Module for controlling mpv"""
import subprocess
import logging

logger = logging.getLogger(__name__)

class Mpv:
  """Main class"""
  __flags_match = {
      'nosound': '--no-audio',
      'verbose': '-v',
      'stereo': '--audio-channels=stereo',
  }

  def __init__(self, args: dict = None):
    self.args = {}
    for key in Mpv.__flags_match.keys():
      self.args[key] = False
    if args is not None:
      self.args.update(args)

  def get_args(self):
    return self.args.copy()

  def set_args(self, args: dict):
    if args:
      self.args.update(args)

  def toggle_sound(self):
    self.args["nosound"] = not self.args["nosound"]

  def play(self, file: str):
    cmd = ['/usr/bin/env', 'mpv', '-fs']
    for key, value in self.args.items():
      # if key.endswith(('cache', 'alang', 'slang', 'sid', 'aid')):
      if key in Mpv.__flags_match.keys():
        cmd.append(Mpv.__flags_match[key]) if value else None
      else:
        cmd.append(f'--{key}={value}') if value else None

    cmd.append(file)
    logger.debug(cmd)
    subprocess.run(cmd)
