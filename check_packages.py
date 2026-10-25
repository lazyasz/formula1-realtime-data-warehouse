import sys
print("Python version:", sys.version)

for mod in ['pandas', 'numpy', 'sklearn', 'xgboost', 'lightgbm', 'scipy']:
    try:
        __import__(mod)
        print(f"{mod}: available")
    except ImportError as e:
        print(f"{mod}: NOT installed ({e})")
