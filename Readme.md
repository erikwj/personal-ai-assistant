### Prerequisites

- Mac M1/M2/M3
- XCode installed
- NodeJS installed
- Python3.11 installed

## Install/Run Backend

Make sure the GGUF model file is in the llm-assistant-backend/app/models folder.

GGUF models can be found on Huggingface.co. Or [click to download](https://huggingface.co/MaziyarPanahi/Qwen2-7B-Instruct-GGUF/resolve/main/Qwen2-7B-Instruct.Q6_K.gguf?download=true) a model.

``` bash

cd llm-assistant-backend

./prepare_python.sh

source .venv/bin/activate


# to run the API
python run.py

```

## Install/Run DocStore


Open a new terminal

``` bash

cd llm-assistant-docstore

./prepare_python.sh

source .venv/bin/activate

# download the embedding model

python models/download_model.py

# load the context documents in the vector database

python load_documents.py

# to run the API
python run.py
```

## Install/Run Frontend

Open a new terminal

``` bash

cd llm-assistant-frontend

npm install

npm run dev
```

Go to http://localhost:8000 in the browser


