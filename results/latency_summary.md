# Latency Summary

Status: Pending

Real classify-to-route latency was not measured in this pass.

Reason:

- A live STM32 serial latency run was not performed from this artifact-generation pass because it would send repeated physical `SORT` commands to the connected hardware path.

To generate the real latency artifacts after the Python environment is ready and the STM32 is flashed and connected, run:

```powershell
python src/measure_latency.py --port COM6 --image data/test/recycling/example.jpg --class recycling --trials 30
```

Expected real output files:

- `results/latency_summary.md`
- `results/latency_summary.csv`

No latency number is claimed until that command completes successfully against the actual STM32 hardware path.
