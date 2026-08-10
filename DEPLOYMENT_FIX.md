# V5 deployment fix

## Fixes
1. Swiss Ephemeris dependency changed from the old `pyswisseph` package to the maintained `pysweph` continuation. It keeps the `import swisseph as swe` interface.
2. `packages.txt` adds Linux build tools so Community Cloud can build the native Swiss Ephemeris extension when a prebuilt wheel is unavailable.
3. Market history selection is now passed directly to yfinance instead of fetching a fixed period and filtering afterward.
4. Removed Python bytecode from the upload package.

## Streamlit Cloud
After uploading/replacing the V5 files, wait for dependency installation to finish. If the log still says `pysweph` cannot be installed under Python 3.14, change the app's Python version to 3.13 in Streamlit Advanced settings and redeploy. Community Cloud requires a redeploy to change Python versions.
