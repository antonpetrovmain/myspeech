# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for MySpeech.app"""

import sys
from pathlib import Path

block_cipher = None

# Project root
ROOT = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('resources/menubar_icon.png', 'resources'),
    ],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
        'Quartz',
        'Quartz.CoreGraphics',
        'AppKit',
        'Foundation',
        'objc',
        'sounddevice',
        'numpy',
        'openai',
        'openai.resources',
        'openai.resources.audio',
        'openai.resources.audio.transcriptions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'mlx',
        'mlx_audio',
        'vllm_mlx',
        'transformers',
        'pytest',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MySpeech',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MySpeech',
)

app = BUNDLE(
    coll,
    name='MySpeech.app',
    icon='resources/MySpeech.icns',
    bundle_identifier='com.myspeech.app',
    info_plist={
        'CFBundleName': 'MySpeech',
        'CFBundleDisplayName': 'MySpeech',
        'CFBundleVersion': '0.2.11',
        'CFBundleShortVersionString': '0.2.11',
        'LSMinimumSystemVersion': '13.0',
        'NSMicrophoneUsageDescription': 'MySpeech needs microphone access to record your voice for transcription.',
        'NSAppleEventsUsageDescription': 'MySpeech needs automation access to paste transcribed text.',
        'NSHighResolutionCapable': True,
        'LSUIElement': False,
    },
)
