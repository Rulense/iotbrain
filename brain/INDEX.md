# Jetson Brain Index

One line per entry. Format: `- [title](domain/slug.md) — type · JP range · hook`

## ml-stack
- [ImportError: libcudnn.so after pip-installing PyTorch on Jetson](ml-stack/pytorch-wheel-libcudnn-import-error.md) — fix · JP 5.x–6.x · wheel/JetPack mismatch breaks import or CUDA
- [Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)](ml-stack/pytorch-jetpack6-working-wheels.md) — config · JP 6.x · jp6/cu126 pip index, no source builds

## runtime
- [Default power mode silently caps Jetson performance](runtime/default-power-mode-caps-performance.md) — gotcha · JP all · nvpmodel + jetson_clocks before benchmarking
