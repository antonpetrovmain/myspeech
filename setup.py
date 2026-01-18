"""
Setup script for building MySpeech.app using py2app.

Usage:
    python setup.py py2app
"""

from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'resources/MySpeech.icns',
    'plist': {
        'CFBundleName': 'MySpeech',
        'CFBundleDisplayName': 'MySpeech',
        'CFBundleIdentifier': 'com.myspeech.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '13.0',
        'NSMicrophoneUsageDescription': 'MySpeech needs microphone access to record your voice for transcription.',
        'NSAppleEventsUsageDescription': 'MySpeech needs automation access to paste transcribed text.',
        'LSUIElement': False,  # Show in Dock
    },
    'packages': [
        'myspeech',
        'pynput',
        'sounddevice',
        'numpy',
        'openai',
    ],
    'includes': [
        'Quartz',
        'AppKit',
        'Foundation',
    ],
    'excludes': [
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
    ],
}

setup(
    name='MySpeech',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
