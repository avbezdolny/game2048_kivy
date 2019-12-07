# -*- mode: python -*-
from kivy_deps import sdl2, glew, gstreamer
block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Projects\\kivyframework\\2048_kivy'],
             binaries=[],
             datas=[('game2048.kv', '.'), ('Rubik.ttf', '.'), ('click.wav', '.'), ('popup.wav', '.'), ('data/*.png', 'data')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz, Tree('C:\\Projects\\kivyframework\\2048_kivy'),
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + gstreamer.dep_bins)],
          name='game2048',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False, icon='C:\\Projects\\kivyframework\\2048_kivy\\game2048.ico' )
