# VoxLabs benchmark: run

Intel64 Family 6 Model 186 Stepping 2, GenuineIntel · NVIDIA GeForce RTX 4050 Laptop GPU, 6141 MiB, 610.88 · Windows-11-10.0.26300-SP0 · device=auto

| Engine | Device | Cold total (s) | Load (s) | Scenario | Wall (s) | Audio (s) | RTF | Inference (s) | Post (s) | Save (s) | Register (s) | Other (s) | Peak VRAM (MB) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| piper-en-us-lessac-medium | cpu | 7.032 | 2.278 | first | 3.048 | 4.32 | 0.706 | 3.026 | 0.0 | 0.005 | 0.013 | 0.004 | 0 |
| | | | | short | 0.21 | 4.27 | 0.049 | 0.183 | 0.0 | 0.007 | 0.014 | 0.006 | |
| kokoro-82m | cuda:0 | 56.507 | 47.738 | first | 7.335 | 4.74 | 1.547 | 7.277 | 0.001 | 0.022 | 0.022 | 0.013 | 863 |
| | | | | short | 0.242 | 4.74 | 0.051 | 0.175 | 0.001 | 0.038 | 0.022 | 0.006 | |
