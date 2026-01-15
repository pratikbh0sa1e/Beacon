# Enable GPU Acceleration for OCR

## Changes Made

### 1. Enabled GPU in EasyOCR Engine
- **File**: `backend/utils/ocr/easyocr_engine.py`
- **Change**: Line 21 changed from `gpu=False` to `gpu=True`

## Installation Steps

### Install PyTorch with CUDA 11.8 Support

Since you have CUDA 11.8 and cuDNN installed, run this command in your virtual environment:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

This will:
- Install PyTorch compiled with CUDA 11.8 support
- Install torchvision and torchaudio with matching CUDA support
- Replace any existing CPU-only PyTorch installation

### Verify GPU is Available

After installation, verify GPU is detected:

```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Expected output:
```
CUDA Available: True
CUDA Version: 11.8
GPU Device: [Your GPU Name]
```

## Testing the OCR System

### 1. Restart Backend Server
```bash
# Stop current server (Ctrl+C)
# Start again
uvicorn backend.main:app --reload
```

### 2. Test with Document Upload
- Upload a scanned PDF document
- Check backend logs for OCR processing
- GPU acceleration should significantly speed up processing (2-5x faster)

### 3. Monitor GPU Usage
While OCR is running, check GPU usage:
```bash
nvidia-smi
```

## Performance Expectations

### CPU vs GPU Processing Times (approximate)
- **Single page (CPU)**: 3-5 seconds
- **Single page (GPU)**: 0.5-1.5 seconds
- **10-page document (CPU)**: 30-50 seconds
- **10-page document (GPU)**: 5-15 seconds

## Troubleshooting

### If GPU is not detected:
1. Verify CUDA installation: `nvcc --version`
2. Verify cuDNN is installed
3. Check PyTorch CUDA version matches your CUDA: `python -c "import torch; print(torch.version.cuda)"`
4. Reinstall PyTorch with correct CUDA version

### If you get CUDA out of memory errors:
- EasyOCR loads models into GPU memory (~1-2GB)
- Reduce batch size or process fewer pages at once
- Close other GPU-intensive applications

### Fallback to CPU:
If GPU issues persist, change back to `gpu=False` in `easyocr_engine.py`

## Next Steps

1. Install PyTorch with CUDA support (command above)
2. Restart backend server
3. Test with scanned documents
4. Monitor performance improvements
5. Verify rotation detection and table extraction work correctly
