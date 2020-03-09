# -*- mode: python -*-

block_cipher = None


a = Analysis(['FEALink.py'],
             pathex=['/Users/rarata/Google Drive/ME 309/Project/FEALink'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='FEALink',
          debug=False,
          strip=False,
          upx=True,
          console=False )
app = BUNDLE(exe,
             name='FEALink.app',
             icon=None,
             bundle_identifier=None)
