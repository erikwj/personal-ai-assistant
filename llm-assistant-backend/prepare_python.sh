#! /bin/bash

python3.11 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

CMAKE_ARGS='-DLLAMA_METAL=on' pip install --force-reinstall llama-cpp-python