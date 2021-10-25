# simple-dali
Datalink in pure python.

Protocol is defined at
https://iris-edu.github.io/libdali/datalink-protocol.html

# build/release
```
conda create -n simpledali python=3.9
conda activate simpledali
python3 -m pip install --upgrade build
python3 -m build
pip install dist/simpledali-0.0.1-py3-none-any.whl --force-reinstall
```

# maybe one day conda package:
```
conda install conda-build
```
