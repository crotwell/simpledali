
# build/release
```
conda create -n simpledali python=3.9
conda activate simpledali
python3 -m pip install --upgrade hatch
pytest
hatch clean
hatch build
pip3 install dist/simpledali-*-py3-none-any.whl --force-reinstall
pytest
```

for testing, use code in current directory so updates on edit:
```
pip install -v -e .
```

Hints on publish:
https://packaging.python.org/en/latest/tutorials/packaging-projects/

```
python3 -m pip install --upgrade hatch
hatch clean && hatch build
pytest
# update release/version in docs/source/conf.py
cd docs ; make html && open build/html/index.html ; cd ..
git status
hatch publish
```

# maybe one day conda package:
```
conda install conda-build
```
