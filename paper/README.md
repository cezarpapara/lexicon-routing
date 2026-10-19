# paper/

Scripts that collect the numbers of the tables and draw the figures of the paper from the runs in
`data/results`, so that every value in the article can be traced back to a run:

```bash
python paper/make_results.py    # data/results -> paper/results.json (tables, per-instance values)
python paper/make_figures.py    # paper/results.json + data/instances -> paper/figs/fig*.png
```

Run them from the repository root after `python -m app.cli report`. Both need the dependencies of
the application (`requirements.txt`); the figures need matplotlib.
