# Graphs

## runtime_plot.py

Produce a graph for a particular CSV that was generated with rutite.py  

If --temp-sensor is specified, then the x-axis will display Temperature (C).  

For example:
```
python3 runtime_plot.py \
  --lux-to-lumen-factor 4.336 \
  --temp-sensor mcp9808 \
  --inputfile vezerlezer_ed10_turbo_2hr.csv \
  --graph-title 'Flashlight Turbo' \
  --graph-subtitle 'Battery' \
  --duration-max 7200 --duration-major 600 --duration-minor 300 \
  --watermark-x 0.08 --watermark-y 0.3 \
  --watermark "Author Watermark"
```

![runtime_plot](https://github.com/TimMcMahon/RuTiTe/blob/master/flashlight_turbo.png)

## multi_runtime_plot.py

Produce a graph with multiple CSV files that were genernated with rutite.py  

Edit `multi_runtime_plot.py` to specify the filenames and add and remove subplots as you see fit.   

```
python3 multi_runtime_plot.py \
  --lux-to-lumen-factor 4.336 \
  --graph-title 'Flashlight' \
  --graph-subtitle 'Battery' \
  --duration-max 12600 --duration-major 1800 --duration-minor 300 \
  --watermark-x 0.1 --watermark-y 0.15 \
  --watermark "Author Watermark"
```

![multi_runtime_plot](https://github.com/TimMcMahon/RuTiTe/blob/master/flashlight.png)
