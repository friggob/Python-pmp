from cmd import Cmd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Cli(Cmd):
  prompt = "Do? "
  def __init__(self, completekey = "tab", stdin = None, stdout = None,
               player = None, playlist = None, default_actions = None,
               no_autostart = False):
    super().__init__(completekey, stdin, stdout)
    self.player          = player
    self.playlist        = playlist
    self.default_actions = default_actions or {}
    self.save            = True
    self.move            = True
    self.autostart       = not no_autostart

  def do_search(self, arg):
    """Search for file in playlist"""
    num_width = len(str(len(self.playlist)))
    for idx, item in enumerate(self.playlist):
      if arg in item.filename:
        print(f"{idx: >{num_width}} : {item.filename}")

  def do_nosound(self, _):
    """Toggle audio"""
    self.player.toggle_sound()

  def do_q(self, _):
    """Quit"""
    return True

  def do_x(self, _):
    """Quit without saving playlist even if flag is set"""
    self.save = False
    return True

  def do_y(self, dest):
    """Delete file unless nodelete flag is sett"""
    self._delete(dest)
    return self.play_next()

  do_a = do_y

  def do_yq(self, dest):
    """Delete file unless nodelete flag is sett and quit"""
    self._delete(dest)
    return self.do_nmq(dest)

  def do_yx(self, dest):
    """Delete file unless nodelete flag is sett and quit without saving playlist"""
    self._delete(dest)
    return self.do_x(dest)

  def do_g(self, _):
    """Move file to ./_gg/"""
    return self.do_m('_gg')

  def do_gq(self, _):
    """Move file to ./_gg/ and quit"""
    self._move_file("_gg")
    return self.do_nmq(None)
  
  def do_gx(self, _):
    """Move file to ./_gg/ and quit without saving playlist"""
    self._move_file("_gg")
    return self.do_nmx(None)

  def do_ng(self, _):
    """Move file to ./ngg/"""
    return self.do_m("ngg")

  def do_ngq(self, _):
    """Move file to ./ngg/ and quit"""
    self._move_file("ngg")
    return self.do_nmq(None)

  def do_ngx(self, _):
    """Move file to ./ngg/ and quit without saving playlist"""
    self._move_file("ngg")
    return self.do_nmx(None)
  
  def do_m(self, dest):
    """Move file"""
    self._move_file(dest)
    return self.play_next()

  def do_mq(self, dest):
    """Move file and quit"""
    self._move_file(dest)
    return self.do_nmq(None)
  
  def do_mx(self, dest):
    """Move file and quit without saving playlist"""
    self._move_file(dest)
    return self.do_nmx(None)

  def do_sort(self, _):
    """Sort playlist"""
    self.playlist.sort()
  
  def do_z(self, _):
    """Shuffle playlist"""
    self.playlist.shuffle()
  
  def do_l(self, _):
    """List all entries in playlist"""
    num_width = len(str(len(self.playlist)))
    for idx, item in enumerate(self.playlist):
      prefix = "*" if self.playlist.get_next_index() == idx else ""
      print(f"{prefix:<1}{idx: >{num_width}} : {item.filename}")

  def do_r(self, _):
    """Replay file"""
    self.playlist.replay()
    self.play_next()

  def do_s(self, filename = None):
    """Save playlist to file"""
    filename = filename or None
    print("Saving playlist to file")
    self.playlist.save_list(filename)

  def do_sq(self, filename):
    """Save playlist to file and quit"""
    self.do_s(filename)
    return self.do_x(None)

  def do_p(self, _):
    """Print out player options"""
    for key, val in self.player.get_args().items():
      print(f"{key:<10}{val}")

  def do_nm(self, _):
    """Play next file without moving previous file even if flag is sett"""
    return self.play_next()

  def do_nmq(self, _):
    """Quit without moving previous file even if flag is sett"""
    self.move = False
    return True

  def do_nmx(self, _):
    """Quit without move file or saving playlist"""
    self.move = False
    self.save = False
    return True

  def do_details(self, _):
    """Show details of current file"""
    print(self.playlist.get_current().details())

  def do_EOF(self, _):
    self.move = False
    self.save = False
    print()
    return True

  def play_next(self):
    if (next_to_play := self.playlist.get_next()) is None:
      print("No more files to play!")
      return True
    else:
      logger.debug(f'play_next(): {next_to_play}')
      print('-'*20)
      print(f"Playing #{self.playlist.index(next_to_play)}, '{next_to_play.filename}'")
      print()
      self.player.play(next_to_play.fullpath)
      logger.debug(f'play_next(): {next_to_play}')
    return False

  def _delete(self, _=None):
    if not self.default_actions.get("nodelete"):
      self._move_file(".delete")

  def _move_file(self, dest = None, postfix = ""):
    current_file = self.playlist.get_current()
    filename     = current_file.filename + postfix
    move_path    = dest or (self.default_actions.get("move_file_dir") or "sett")
    dest_dir     = Path(move_path)
    dest_path    = Path(move_path + "/" + filename)
    src          = current_file.fullpath
    relpath      = current_file.relpath

    if dest_dir.exists() and not dest_dir.is_dir():
      print(f"{dest} already exists and is not a directory!")
      print("Not moving the file!")
      return False
    else:
      dest_dir.mkdir(exist_ok=True)

    if dest_path.exists():
      from filecmp import cmp
      if cmp(src, dest_path, shallow=False):
        print("File already exists and is the same! Moving file to .delete/")
        if dest == ".delete":
          src.unlink()
        else:
          self._move_file(".delete")
      else:
        self._move_file(dest, ".notsame")
    else:
      print(f"Moving {relpath} -> {dest_dir}")
      print("-----------")
      src.rename(dest_path)
      self.playlist.remove()
      
  def emptyline(self):
    if self.default_actions.get("move_delete"):
      logger.info(f'Automatically moving file to ./.delete/')
      self._delete()
    elif self.default_actions.get("move_files"):
      logger.info(f'Automatically move files to move directory')
      self._move_file()
    # if self.playlist.get_next():
    #   logger.info(f"{self.playlist.get_current()=}")
    # else:
    #   self.move = False
    #   self.save = False
    return self.play_next()

  def default(self, arg):
    """What to do if no defined action"""
    args = arg.split(" ")
    farg = args[0]
    sarg = None if len(args) < 2 else args[1]
    logger.info(f"{farg=}")
    num = int(farg) if farg.lstrip("-+").isdecimal() else -1
    logger.info(f"{num=}")
    if num > -1 and num < len(self.playlist):
      self.playlist.set_current(num)
      if len(args) > 1 and sarg[0] == "p":
        return self.play_next()
    elif num != -1:
      print(f"Nu such index in playlist: {farg}")
    else:
      print(f"No such command: {arg}")
    return False
  
  def preloop(self):
    if not self.playlist:
      print("No files to play!")
      raise SystemExit()
    if self.autostart:
      self.play_next()

  def cmdloop(self):
    if self.default_actions.get("continuous"):
      while not self.play_next():
        pass
    else:
      return super().cmdloop()  
      
  def postloop(self):
    try:
      if self.default_actions.get("move_delete") and self.move:
        self._delete()
        pass
      elif self.default_actions.get("move_files") and self.move:
        self._move_file(None)
        pass
    except (FileNotFoundError, AttributeError):
      pass
    if self.default_actions.get("save_playlist") and self.save:
      self.do_s()
    print("Bye bye!")
