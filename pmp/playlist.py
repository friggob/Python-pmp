import asyncio
import random
import json
import logging
from .file import File

logger = logging.getLogger(__name__)

class PlayList(list):
  def __init__(self, files = None, init_states: dict = None ):
    self.init_states = init_states or {}
    self.start_pos   = self.init_states.get('start_pos') or 0

    super().__init__(asyncio.run(self.__init_playlist(files)))

    if self.init_states.get('randomize', False):
      self.shuffle()

    self._start(self.start_pos)

  def _start(self, start_pos = 0):
    if len(self) <= 0 or start_pos > len(self):
      self._previous_file  = None
      self._next_file      = None
    else:
      self._previous_file  = None if start_pos == 0 else self[start_pos - 1]
      self._next_file      = None if start_pos == len(self) else self[start_pos]

  def get_next(self):
    next_file = self._next_file
    if next_file is not None:
      index = self.index(next_file)
      if index < (len(self) - 1):
        self._next_file = self[index + 1]
      else:
        self._next_file = None
      self._previous_file = next_file

    return next_file

  def get_next_index(self):
    return None if self._next_file is None else self.index(self._next_file)

  def get_current(self):
    return self._previous_file or self._next_file

  def set_current(self, num: int):
    if num >= 0 or num < len(self):
      self._start(num)
    else:
      raise ValueError

  def shuffle(self):
    random.shuffle(self)
    self._start(start_pos = 0)

  def replay(self):
    if self._previous_file is not None:
      index = self.index(self._previous_file)
    elif self._next_file is not None:
      index = 0
    else:
      return None

    self._start(start_pos = index)

  def sort(self, *args, **kwargs):
    super().sort(*args, **kwargs)
    self._start(start_pos = 0)

  def remove(self):
    if (current_file := self.get_current()) is not None:
      index = self.index(current_file)
    else:
      return None
    del self[index]
    self._start(start_pos = index)

  def export_as_json(self):
    return json.dumps([x.as_dict() for x in self])

  def save_list(self, file_path = None):
    path = file_path if file_path else '__pl.json'

    logger.info(f"Saving playlist to file: {path}")

    save_data = {
      "type": "Fredriks playlist save file",
      "next_to_play": self.index(self.get_current()) or 0,
      "next_filename": self._next_file.filename or "",
      "data": json.loads(self.export_as_json()),
    }
    json.dump(save_data, open(path, 'w'), indent=2)

  def import_json_playlist(self, filename):
    file_list = list()
    list_dict = json.load(open(filename))

    logger.debug(json.dumps(list_dict, indent=2))

    print(list_dict.get("next_to_play"))
    self.start_pos = list_dict.get("next_to_play", 0)
    for entry in list_dict.get("data"):
      file_list.append(entry.get("fullpath"))

    return file_list

  async def __init_playlist(self, files: list = None):
    list_of_files = []

    if not files:
      return list_of_files

    for filename in files:
      try:
        file = await File.create_object(filename)
      except ValueError as msg:
        logger.debug(msg)
      else:
        logger.info(file.mime)
        mime = file.mime.split("/")

        if mime[0] == "text" or file.filename == '__savefile':
          continue
        if file.filename == '__pl.json' and mime[1] == 'json':
          logger.info("JSON playlist file!")
          list_of_files.extend(
            await self.__init_playlist(self.import_json_playlist(file.fullpath))
          )
          continue
        if any(x.fullpath == file.fullpath for x in list_of_files):
          logger.info(f"'{filename}' already in playlist")
          continue
        if mime[0] in ('audio', 'video'):
          list_of_files.append(file)

    return list_of_files.copy()
