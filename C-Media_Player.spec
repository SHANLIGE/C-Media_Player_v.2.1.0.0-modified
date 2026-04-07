# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['App/App.py'],
             pathex=["/cmediaplayerlinux/cod/C-Media_Linux_player-master/entorno6/lib/python3.10/site-packages/cv2"],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=["."],
             hooksconfig={},
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
          name='CMedia_Player',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,          
          )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='C-Media_Player')
