import json
import magic
from pathlib import Path
from mimetypes import guess_type


async def get_mime_type(filename):
  mime_type = guess_type(filename)[0]
  #mime_type = None
  if mime_type is None or mime_type.split('/')[0] == 'text':
    mime_type = magic.detect_from_filename(filename).mime_type
  return mime_type

class File(Path):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    if self.is_file():
      self.fullpath = Path(self).resolve()
      self.filename = Path(self).name
      self.dirname  = self.fullpath.parent
      self.relpath  = Path(self).resolve().relative_to(Path.cwd(), walk_up=True)
      self.mime     = None
    else:
      raise ValueError("Path must point to a valid file")

  async def _mime(self):
    self.mime = await get_mime_type(self.fullpath)

  @classmethod
  async def create_object(cls, path):
    obj = cls(path)
    await obj._mime()
    return obj

  def details(self):
    details = {
      'Fullpath': str(self.fullpath),
      'Filename': str(self.filename),
      'Directory': str(self.dirname),
      'Path relative to CWD': str(self.relpath),
      'Mime-type': str(self.mime)
    }
    return json.dumps(details, indent=2)

  def as_dict(self):
    return {
      'fullpath': str(self.fullpath),
      'filename': str(self.filename),
      'dirname': str(self.dirname),
      'relpath': str(self.relpath),
      'mime': str(self.mime)
    }
