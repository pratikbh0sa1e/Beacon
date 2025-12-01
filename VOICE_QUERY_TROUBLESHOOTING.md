# Voice Query Troubleshooting - WinError 2

## Error: "The system cannot find the file specified"

This error occurs when Whisper or FFmpeg cannot be found on your system.

---

## Quick Fix Options

### Option 1: Install FFmpeg (Required for Whisper)

**Windows:**

1. Download FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. Extract to `C:\ffmpeg`
3. Add to PATH:
   - Open System Properties → Environment Variables
   - Edit "Path" variable
   - Add: `C:\ffmpeg\bin`
4. Restart terminal/IDE
5. Test: `ffmpeg -version`

**Or use Chocolatey:**

```bash
choco install ffmpeg
```

**Or use Scoop:**

```bash
scoop install ffmpeg
```

---

### Option 2: Install Whisper Model

The Whisper model might not be downloaded yet.

**Install/Update:**

```bash
pip install --upgrade openai-whisper
```

**Test Whisper:**

```python
import whisper
model = whisper.load_model("base")
print("Whisper loaded successfully!")
```

---

### Option 3: Check Python Environment

Make sure you're in the correct virtual environment:

```bash
# Activate venv
venv\Scripts\activate

# Reinstall whisper
pip install --force-reinstall openai-whisper
```

---

### Option 4: Use Alternative Transcription (Temporary)

If you can't install FFmpeg right now, you can temporarily disable voice queries or use a different transcription service.

**Check backend logs for exact error:**
Look for the full stack trace in your backend terminal to see which file is missing.

---

## Verification Steps

### 1. Check FFmpeg:

```bash
ffmpeg -version
```

Should show version info.

### 2. Check Whisper:

```bash
python -c "import whisper; print(whisper.__version__)"
```

Should print version number.

### 3. Check Python Path:

```bash
python -c "import sys; print(sys.executable)"
```

Should point to your venv.

---

## Common Issues

### Issue 1: FFmpeg Not in PATH

**Solution:** Add FFmpeg to system PATH and restart terminal

### Issue 2: Wrong Python Environment

**Solution:** Activate correct venv before running backend

### Issue 3: Whisper Model Not Downloaded

**Solution:** Run `whisper --help` to trigger model download

### Issue 4: Antivirus Blocking

**Solution:** Add FFmpeg and Python to antivirus exceptions

---

## Alternative: Use OpenAI Whisper API (No FFmpeg Needed)

If you can't install FFmpeg, use OpenAI's API instead:

**1. Update `Agent/voice/speech_config.py`:**

```python
ACTIVE_ENGINE = "whisper-api"  # Use OpenAI API instead of local
```

**2. Add OpenAI API key to `.env`:**

```env
OPENAI_API_KEY=your-openai-api-key
```

**3. Restart backend**

This uses OpenAI's cloud service (costs $0.006/minute) but doesn't require FFmpeg.

---

## Quick Test

After installing FFmpeg, test with this command:

```bash
# Test FFmpeg
ffmpeg -version

# Test Whisper
python -c "import whisper; model = whisper.load_model('base'); print('Success!')"
```

---

## For Now: Disable Voice Queries

If you want to continue without voice queries, you can:

1. Hide the voice buttons in the UI
2. Focus on text chat (which works perfectly)
3. Install FFmpeg later when convenient

---

## Summary

**Most Likely Issue:** FFmpeg not installed or not in PATH

**Quick Fix:**

1. Install FFmpeg
2. Add to PATH
3. Restart terminal
4. Restart backend

**Alternative:** Use OpenAI Whisper API (no FFmpeg needed)

**For Now:** Text chat works perfectly, voice can wait!
