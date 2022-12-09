# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['mcpPY.py'],
             pathex=['C:\\Users\\SUNDYN\\PycharmProjects\\pythonProject'],
             binaries=[],
             datas=[('I_O','I_O'),
                    ('igorwriter','igorwriter')],
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
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='mcpPy',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='mcpPY')
