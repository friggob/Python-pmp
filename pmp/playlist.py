import random
import asyncio
import json
import logging
from .file import File
logger = logging.getLogger(__name__)

class PlayList(list):
  def __init__(self, files = None, init_states: dict = None):
    self.randomize     = init_states.get('randomize') if init_states else False
    self.list_position = init_states.get('start_pos', None) if init_states else None
    super().__init__(asyncio.run(self.__init_playlist(files)))
    self.list_position = 0 if self.list_position is None else self.list_position
    
    if self.randomize:
      self.shuffle()

  async def __init_playlist(self, files: list = None):
    file_list = []
    if files is None:
      return None
    
    for filename in files:
      try:
        logger.debug(f'{filename=}')
        file = await File.create_object(filename)
      except ValueError as msg:
        logger.debug(f'ValueError: {msg}')
        pass
      else:
        if file.mime.split('/')[0] == 'text':
          continue
        if file.filename == '__savefile':
          continue
        if file.filename == '__pl.json':
          file_list.extend(
            await self.__init_playlist(self.import_json_playlist_file(file.fullpath))
          )
          self.randomize = False
          continue
        if any(x.fullpath == file.fullpath for x in file_list):
          logger.info(f"'{filename}' already in playlist")
          continue
        if file.mime.split('/')[0] in {'audio', 'video', 'image'}:
          file_list.append(file)
    return file_list

  def shuffle(self):
    self.list_position = 0
    random.shuffle(self)

  def get_list(self):
    return self.copy()

  def get_current_file(self):
    assert self.list_position >= 0,\
      f"list_position should never be negative ({self.list_position = })"
    if self:
      pos = self.list_position if self.list_position == 0 else (self.list_position - 1)
      return self[pos]
    else:
      return None

  def remove(self, arg):
    super().remove(arg)
    self.list_position -= 1
    assert self.list_position >= 0

  def get_next_file(self):
    if (self.list_position + 1) <= len(self):
      self.list_position += 1
      return self[self.list_position - 1]
    else:
      return None
  
  def import_json_playlist_file(self, filename):
    file_list = []
    with open(filename) as file:
      list_dict = json.load(file)

    logger.debug(f'{self.list_position = }')
    logger.debug(json.dumps(list_dict, indent=2))
    if self.list_position is None:
      self.list_position = list_dict.get('next_to_play', 0)

    for entry in list_dict.get('data'):
      file_list.append(entry.get('fullpath'))

    logger.info(f'{self.list_position = }')

    return file_list

  def export_as_json(self):
    return json.dumps([x.as_dict() for x in self])

  def save_list(self, file_path = None):
    if file_path is None or not file_path:
      path = '__pl.json'
    else:
      path = file_path

    logger.info(f'Saving playlist to file: {path}')

    save_data = {}
    save_data['type'] = 'Fredriks playlist save file'
    save_data['next_to_play'] = self.list_position
    try:
      save_data['next_filename'] = self[self.list_position].filename
    except IndexError:
      pass

    save_data['data'] = json.loads(self.export_as_json())
    json.dump(save_data, open(path, 'w'), indent=2)
