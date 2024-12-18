from sentence_transformers import SentenceTransformer

def download_model():
    # This will download and cache the model
    model = SentenceTransformer('all-mpnet-base-v2')
    # Save the model to local directory
    model.save('models/embeddings')

if __name__ == "__main__":
    download_model() 