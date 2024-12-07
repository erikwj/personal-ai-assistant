from sentence_transformers import SentenceTransformer
import os

def download_model():
    # Create models directory
    model_name = "sentence-transformers/all-mpnet-base-v2"  # or any other model you want to use
    output_dir = "models/embeddings"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading model: {model_name}")
    
    try:
        # Download model
        model = SentenceTransformer(model_name)
        
        # Save the model locally
        model.save(output_dir)
        print(f"Model saved to {output_dir}")
        
    except Exception as e:
        print(f"Error downloading model: {str(e)}")

if __name__ == "__main__":
    download_model() 