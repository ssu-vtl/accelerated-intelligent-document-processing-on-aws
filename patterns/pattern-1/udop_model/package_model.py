import os
import torch
import shutil
import tarfile
from transformers import UdopModel, AutoProcessor
from pathlib import Path

def package_for_sagemaker(inference_code_dir="inference_code", output_dir="sagemaker_package"):
    """
    Downloads the UDOP model and packages it with inference code from specified subdirectory
    """
    # First clean up any existing directories
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    # Create directory structure
    os.makedirs(os.path.join(output_dir, "model"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "code"), exist_ok=True)
    
    # Verify inference code directory exists
    if not os.path.exists(inference_code_dir):
        raise FileNotFoundError(f"Inference code directory '{inference_code_dir}' not found")
    
    print("Downloading model and processor...")
    # Download model and processor
    model = UdopModel.from_pretrained("nielsr/udop-large")
    processor = AutoProcessor.from_pretrained("nielsr/udop-large", apply_ocr=False)
    
    # Save model state dict
    print("Saving model state dict...")
    model_path = os.path.join(output_dir, "model", "model.pth")
    torch.save(model.state_dict(), model_path)
    
    # Save processor
    print("Saving processor...")
    processor.save_pretrained(os.path.join(output_dir, "model"))
    
    # Copy all required files from inference_code directory
    print("Copying inference code files...")
    required_files = ["inference.py", "utils.py", "udop.py", "requirements.txt"]
    
    for file in required_files:
        source_path = os.path.join(inference_code_dir, file)
        if os.path.exists(source_path):
            shutil.copy(source_path, os.path.join(output_dir, "code", file))
        else:
            raise FileNotFoundError(f"{file} not found in {inference_code_dir}")
    
    # Remove old tar file if it exists
    if os.path.exists("model.tar.gz"):
        os.remove("model.tar.gz")
    
    # Create tar.gz file with correct directory structure
    print("Creating tar.gz archive...")
    with tarfile.open("model.tar.gz", "w:gz") as tar:
        # Change directory to output_dir to avoid including full path
        original_dir = os.getcwd()
        os.chdir(output_dir)
        
        # Add directories without parent directory
        tar.add("model")
        tar.add("code")
        
        # Return to original directory
        os.chdir(original_dir)
    
    print(f"SageMaker model package created: model.tar.gz")
    print(f"Package contents:")
    with tarfile.open("model.tar.gz", "r:gz") as tar:
        tar.list()
    
    # Clean up temporary directory
    shutil.rmtree(output_dir)

if __name__ == "__main__":
    package_for_sagemaker()