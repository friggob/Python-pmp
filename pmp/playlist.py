import asyncio
import logging
import random
import json
from .file import File

logger = logging.getLogger(__name__)

class PlayList(list):
  def __init__(self, files = None, init_states: dict = None):
    self.init_states   = init_states or {}
    self.start_pos     = self.init_states.get('start_pos') or 0
    self.randomize     = self.init_states.get('randomize', False)
    logger.debug(f'{init_states=}')

    super().__init__(asyncio.run(self.__init_playlist(files)))

    if self.randomize:
      self.shuffle()
      
    self._set_start_files()
    
  def _set_start_files(self):
    if len(self) <= 0 or self.start_pos > len(self):
      self._next_file     = None
      self._previous_file = None
    else:
      self._next_file     = None if self.start_pos == len(self) else self[self.start_pos]
      self._previous_file = None if self.start_pos == 0 else self[self.start_pos - 1]

  def shuffle(self):
    random.shuffle(self)
    self.start_pos = 0
    self._set_start_files()
    
  def get_previous_index(self):
    return None if self._previous_file is None else self.index(self._previous_file)

  def get_next_index(self):
    return None if self._next_file is None else self.index(self._next_file)

  def replay(self):
    self.start_pos = self.get_previous_index()
    self._set_start_files()
  
  def remove(self, item):
    index = self.get_previous_index()
    if index == 0 or index is None:
      self._previous_file = None
      index = 0
    else:
      self._previous_file = self[index - 1]
    super().remove(item)
    self._next_file = self[index] if len(self) > 0 else None
    logger.debug(f'remove(): {index=} {self._next_file=} {self._previous_file=}')

  def sort(self, *args, **kwargs):
    super().sort(*args, **kwargs)
    self.start_pos = 0
    self._set_start_files()

  @property
  def current_file(self):
    return self.get_current_file()

  @property
  def next_file(self):
    return self._next_file

  def get_current_file(self):
    return self._previous_file or self._next_file

  def set_current_file(self, index):
    self.start_pos = index
    self._set_start_files()

  def get_next_file(self):
    index = (len(self) - 1) if self.get_next_index() is None else self.get_next_index()
    logger.debug(f"get_next_file(): {index=}")
    self._previous_file = self._next_file
    self._next_file = None if (index + 1) >= len(self) else self[index + 1]

    return self._previous_file

  def export_as_json(self):
    return json.dumps([x.as_dict() for x in self])

  def save_list(self, file_path = None):
    path = file_path if file_path else '__pl.json'

    logger.info(f"Saving playlist to file: {path}")

    save_data = {}
    save_data['type'] = "Fredriks playlist save file"
    save_data['next_to_play'] = self.get_next_index() or (len(self) - 1)
    save_data['next_filename'] = self._next_file.filename or ""
    save_data['data'] = json.loads(self.export_as_json())
    json.dump(save_data, open(path, 'w'), indent=2)

  def import_json_playlist(self, filename):
    file_list = list()
    with open(filename) as file:
      list_dict = json.load(file)

    logger.debug(json.dumps(list_dict, indent=2))

    print(list_dict.get("next_to_play"))
    self.start_pos = list_dict.get("next_to_play", 0)
    
    for entry in list_dict.get('data'):
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

        if mime[0] ==  "text" or file.filename == '__savefile':
          continue
        if file.filename == '__pl.json' and mime[1] == 'json':
          logger.info("JSON playlist file!")
          list_of_files.extend(
            await self.__init_playlist(self.import_json_playlist(file.fullpath))
          )
          self.randomize = False
          continue
        if any(x.fullpath == file.fullpath for x in list_of_files):
          logger.info(f"'{filename}' already in playlist")
          continue
        if mime[0] in ('audio', 'video'):
          list_of_files.append(file)
          
    return list_of_files.copy()
