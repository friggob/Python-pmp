#!/usr/bin/env python3

import os
import argparse as argp
import logging
from pmp.playlist import PlayList
from pmp.mpv import Mpv
from pmp.cli import Cli

__version__ = "0.1.4"

def main():
  logging.basicConfig(level = os.environ.get('LOGLEVEL', 'WARNING'))
  logger = logging.getLogger('pmp')
  args   = parse_args_setup()
  player = player_setup(args)

  files_to_play = get_files(args)

  playlist = PlayList(files_to_play,
                      {'randomize': args.randomize, 'start_pos': args.start_at})

  cli_args = {
    'nodelete': args.nodelete,
    'continuous': args.q,
    'move_files': args.move_files,
    'move_delete': args.move_delete,
    'save_playlist': args.save_playlist
  }

  if args.move_file_dir:
    cli_args['move_file_dir'] = args.move_file_dir

  prompt = Cli(playlist = playlist, player = player, default_actions = cli_args,
               no_autostart = args.no_autostart)

  if args.save_playlist:
    playlist.save_list()

  try:
    prompt.cmdloop()
  except KeyboardInterrupt:
    print()

def get_files(args):
  if not args.textfile:
    return args.files

  files = []
  for filename in args.files:
    try:
      with open(filename, encoding="UTF-8") as file:
        for line in file:
          files.append(line.rstrip('\r\n'))
    except UnicodeDecodeError:
      print('List of files to play in text file must be UTF-8 encoded!')
      raise SystemExit

  return files

def player_setup(args):
  player = Mpv()
  player_args = player.get_args()
  player_args['nosound'] = args.nosound
  player_args['cache']   = args.cache if args.cache is not None else False
  player_args['verbose'] = args.verbose
  player_args['stereo']  = args.stereo
  player_args.update({'slang': args.subtitle_language}) if args.subtitle_language else None
  player_args.update({'alang': args.audio_language}) if args.audio_language else None
  player_args.update({'sid': args.subtitle_id}) if args.subtitle_id else None
  player_args.update({'aid': args.audio_id}) if args.audio_id else None
  player.set_args(player_args)

  return player

def parse_args_setup():
  parser = argp.ArgumentParser(description='Playlist player')

  parser.add_argument('-n', '--nosound', action='store_true', default=False,
                   help='Play file without sound')
  parser.add_argument('-z', '--randomize', action='store_true', default=False,
                   help='Randomize playlist')
  parser.add_argument('-x', '--save-playlist', action='store_true', default=False,
                   help='Save playlist to disk after playing each file')
  parser.add_argument('-d', '--move-delete', action='store_true', default=False,
                   help='Move files to ./.delete dir after playing by default')
  parser.add_argument('-m', '--move-files', action='store_true', default=False,
                   help='Move files to ./sett dir after playing')
  parser.add_argument('-M', '--move-file-dir', metavar='move_dir', type=str,
                  help='Move file to dir after playing')
  parser.add_argument('-D', '--nodelete', action='store_true', default=False,
                   help='Do not delete files even if we say so')
  parser.add_argument('-c', '--cache', metavar='<kBytes>', type=int,
                   help='Size of mpv cache in kBytes')
  parser.add_argument('-q', action='store_true', default=False,
                   help='Do not wait between playing files')
  parser.add_argument('-s', '--stereo', action='store_true', default=False,
                   help='Force mpv to use stereo')
  parser.add_argument('-v', '--verbose', action='store_true', default=False,
                   help='Make player be more verbose')
  parser.add_argument('-#', '--start-at', default=-1, type=int,
                   help='Start playing at numbered position')
  parser.add_argument('-t', '--textfile', action='store_true', default=False,
                   help='File on command line are text files with one '+
                   'file per line to play')
  parser.add_argument('files', metavar='<files>', nargs='+',
                   help='Media files or playlist files to play')
  parser.add_argument('-j', '--subtitle_language', default=None, type=str,
                   help='Sets the subtitle language')
  parser.add_argument('-J', '--subtitle_id', default=None, type=int,
                   help='Sets the subtitle language id')
  parser.add_argument('-l', '--audio_language', default=None, type=str,
                   help='Sets the audio language')
  parser.add_argument('-L', '--audio_id', default=None, type=int,
                   help='Sets the audio language id')
  parser.add_argument('-a', '--no_autostart', action='store_true', default=False,
                   help='Do not automatically start playing')
  parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {__version__}',
                   help='Show program version')

  return parser.parse_args()

if __name__ == '__main__':
  main()
