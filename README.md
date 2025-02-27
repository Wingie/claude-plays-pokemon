## Setup

1. Create `.env` file with your Claude API key `CLAUDE_KEY={{key}}`
2. Install GameBoy emulator https://sameboy.github.io/
3. Download and run Pokemon Yellow ROM https://www.emulatorgames.net/roms/gameboy-color/pokemon-yellow-version/
4. Add `WINDOW_TITLE={{title of the emulator window}}` to `.env` file
5. Create Python virtual env `python3 -m venv venv` and activate it `source venv/bin/activate`
6. Install deps `pip install -r requirements.txt`
7. Run `core.py` script `python core.py`
8. Make sure to bring emulator window into view
