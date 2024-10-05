"""CLI module for pmp"""

from pathlib import Path
from cmd import Cmd

class Cli(Cmd):
    prompt = 'Do? '

    def __init__(self, completekey = 'tab', stdin = None, stdout = None,
                 player = None, playlist = None, default_actions = None,
                 no_autostart = False):
        '''Init the class'''
        super().__init__(completekey, stdin, stdout)
        self.player      = player
        self.playlist    = playlist
        self.def_actions = default_actions if default_actions is not None else {}
        self.save        = True
        self.move        = True
        self.autostart   = not no_autostart

    def do_l(self, arg):
        '''List all entries in playlist'''
        num_width = len(str(len(self.playlist)))
        for idx, item in enumerate(self.playlist):
            prefix = '*' if self.playlist.list_position == idx else ''
            print(f'{prefix:<1}{idx: >{num_width}} : {item.filename}')

    def do_search(self, arg):
        '''Search for file in playlist'''
        num_width = len(str(len(self.playlist)))
        for idx, item in enumerate(self.playlist):
            if arg in item.filename:
                print(f' {idx: >{num_width}} : {item.filename}')

    def do_nosound(self, arg):
        '''Toggle nosound flag'''
        flag = not self.player.args['nosound']
        self.player.set_args({'nosound': flag})

    def do_q(self, arg):
        '''Quit'''
        return True
    
    def do_x(self, arg):
        '''Quit without saving playlist even if flag is set'''
        self.save = False
        return True

    def do_y(self, arg):
        '''Delete file unless flag is sett'''
        self._delete(arg)
        return self.play_next()
        
    do_a = do_y
    
    def do_yq(self, arg):
        '''Delete file and quit unless flag is sett'''
        self._delete(arg)
        self.do_nmq(arg)
        
    def do_yx(self, arg):
        '''Delete file and quit unless flag is sett'''
        self._delete(arg)
        self.do_x(arg)
        
    def do_r(self, arg):
        '''Replay file'''
        self.playlist.list_position -= 1
        assert self.playlist.list_position >= 0
        self.play_next()

    def do_z(self, arg):
        '''Shuffle playlist'''
        self.playlist.shuffle()

    def do_s(self, arg):
        '''Save playlist file'''
        filename = arg if arg else None
        print('Saving playlist file.')
        self.playlist.save_list(filename)

    def do_sq(self, arg):
        '''Save playlist file and quit'''
        self.do_s(arg)
        self.do_x(arg)

    def do_p(self, arg):
        '''Print player options'''
        for key, val in self.player.get_args().items():
            print(f'{key:<10}{val}')

    def do_g(self, arg):
        '''Move current file to ./_gg/ and play next'''
        self.do_m('_gg')

    def do_gq(self, arg):
        '''Move current file to ./_gg/ and quit'''
        self._move_file('_gg')
        self.do_nmq(arg)

    def do_gx(self, arg):
        '''Move current file to ./_gg/ and quit'''
        self._move_file('_gg')
        self.do_nmx(arg)

    def do_ng(self, arg):
        '''Move current file to ./ngg/ and play next'''
        self.do_m('ngg')

    def do_ngq(self, arg):
        '''Move current file to ./ngg/ and quit'''
        self._move_file('ngg')
        self.do_nmq(arg)

    def do_ngx(self, arg):
        '''Move current file to ./ngg/ and quit'''
        self._move_file('ngg')
        self.do_nmx(arg)

    def do_m(self, arg):
        '''Move current file and play next'''
        self._move_file(arg)
        return self.play_next()

    def do_mq(self, arg):
        '''Move current file and quit'''
        self._move_file(arg)
        self.move = False
        return True

    def do_nm(self, arg):
        '''Play next file without moving even if flag is sett'''
        return self.play_next()

    def do_nmq(self, arg):
        '''Quit without moving file even if flag is set'''
        self.move = False
        return True
    
    def do_nmx(self, arg):
        '''Quit without moving file or saving playlist even if flags are set'''
        self.move = False
        self.do_x(arg)

    def do_sort(self, arg):
        '''Sort playlist'''
        self.playlist.sort()

    def do_details(self, _):
        '''Show details of current file'''
        print(self.playlist.get_current_file().details())

    def do_EOF(self):
        self.move = False
        self.save = False
        print()
        return True

    def _delete(self, arg):
        if not self.def_actions.get('nodelete'):
            self._move_file('.delete')

    def _move_file(self, arg, postfix = ''):
                
        filename      = self.playlist.get_current_file().filename + postfix
        move_path     = arg if arg else (self.def_actions.get('move_file_dir') or 'sett')
        dest_dir      = Path(move_path)
        dest_path     = Path(move_path + '/' + filename)
        src           = self.playlist.get_current_file().fullpath
        relpath       = self.playlist.get_current_file().relpath

        if dest_dir.exists() and not dest_dir.is_dir():
            print(f'{dest} already exist and is not a directory!!!')
            return False
        else:
            dest_dir.mkdir(exist_ok=True)

        if dest_path.exists():
            from filecmp import cmp
            if cmp(src, dest_path, shallow=False):
                print('File already exists and is the same! Moving to .delete/')
                if arg == '.delete':
                    src.unlink()
                else:
                    self._move_file('.delete')
            else:
                self._move_file(arg, '.notsame')
        else:
            print(f'Moving {relpath} -> {dest_dir}')
            print('-----------')
            src.rename(dest_path)
            self.playlist.remove(self.playlist.get_current_file())

    def emptyline(self):
        '''What to do if empty input'''
        if self.def_actions.get('move_delete'):
            self._move_file('.delete')
        elif self.def_actions.get('move_files'):
            self._move_file('')
        if self.playlist.get_current_file():
            return self.play_next()
        else:
            self.move = False
            self.save = False
            return True

    def default(self, arg):
        '''What to do if no defined action'''
        num = int(arg.split(' ')[0]) if arg.split(' ')[0].lstrip('-+').isdecimal() else -1
        if num > -1 and num < len(self.playlist):
            self.playlist.list_position = num
            if len(arg.split(' ')) > 1 and arg.split(' ')[1][0] == 'p':
                self.play_next()
        elif num != -1:
            print(f"No such index in playlist: {arg}")
        else:
            print(f"No such command: {arg}")
        return False

    def play_next(self):
        if (next_to_play := self.playlist.get_next_file()) is None:
            print('No more files to play!')
            return True
        else:
            print(f'Playing #{self.playlist.index(next_to_play)}, "{next_to_play.filename}"')
            print()
            self.player.play(next_to_play.fullpath)

    def preloop(self):
        if not self.playlist:
            print('No files to play!')
            raise SystemExit()
        if self.autostart:
            self.play_next()

    def postloop(self):
        try:
            if self.def_actions.get('move_delete') and self.move:
                self._delete()
            elif self.def_actions.get('move_files') and self.move:
                self._move_file(None)
        except (FileNotFoundError, AttributeError):
            pass
        if self.def_actions.get('save_playlist') and self.save:
            self.do_s(None)
        print('Bye Bye!')

    def precmd(self, arg):
        return super().precmd(arg)

    def cmdloop(self):
        if not self.def_actions.get('continuous'):
            return super().cmdloop()
        else:
            while not self.play_next():
                pass
