"""Script to copy trained models from Google Drive extraction path to the models/ directory."""

import os
import shutil
from pathlib import Path

# Define paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

# This should match the path used in the notebook
GDRIVE_MODELS_PATH = Path("/content/gdrive/MyDrive/enron_spam_data_extracted")

# Model files to copy
MODEL_FILES = ["model_nb.joblib", "model_lr.joblib"]


def copy_models_from_gdrive():
    """Copy trained models from Google Drive to local models directory."""
    print("Copying trained models from Google Drive to local models directory...")

    # Create models directory if it doesn't exist
    MODELS_DIR.mkdir(exist_ok=True)

    # Copy each model file
    for model_file in MODEL_FILES:
        source = GDRIVE_MODELS_PATH / model_file
        destination = MODELS_DIR / model_file

        if not source.exists():
            print(f"⚠ Warning: {source} not found. Skipping...")
            continue

        shutil.copy2(source, destination)
        print(f"✓ Copied {model_file} to {destination}")

    print("\n✓ Model copying complete!")


def copy_models_from_local(source_dir: str):
    """Copy trained models from a local directory to the models directory.

    Args:
        source_dir: Path to the directory containing the trained models
    """
    print(f"Copying trained models from {source_dir} to local models directory...")

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"❌ Error: Source directory {source_dir} does not exist!")
        return

    # Create models directory if it doesn't exist
    MODELS_DIR.mkdir(exist_ok=True)

    # Copy each model file
    for model_file in MODEL_FILES:
        source = source_path / model_file
        destination = MODELS_DIR / model_file

        if not source.exists():
            print(f"⚠ Warning: {source} not found. Skipping...")
            continue

        shutil.copy2(source, destination)
        file_size = destination.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"✓ Copied {model_file} ({file_size:.2f} MB) to {destination}")

    print("\n✓ Model copying complete!")
    print(f"\nModels are now available in: {MODELS_DIR}")


def verify_models():
    """Verify that model files exist in the models directory."""
    print("\nVerifying model files...")

    all_present = True
    for model_file in MODEL_FILES:
        model_path = MODELS_DIR / model_file
        if model_path.exists():
            file_size = model_path.stat().st_size / (1024 * 1024)
            print(f"✓ {model_file} exists ({file_size:.2f} MB)")
        else:
            print(f"❌ {model_file} missing")
            all_present = False

    if all_present:
        print("\n✓ All model files are present!")
    else:
        print(
            "\n⚠ Some model files are missing. Please train models using the notebook."
        )


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Spam Detection Model Copy Utility")
    print("=" * 60)

    if len(sys.argv) > 1:
        # Copy from specified local directory
        source_dir = sys.argv[1]
        copy_models_from_local(source_dir)
    else:
        # Try to copy from Google Drive path (for Colab environment)
        if GDRIVE_MODELS_PATH.exists():
            copy_models_from_gdrive()
        else:
            print("\nUsage:")
            print("  python copy_trained_models.py <source_directory>")
            print("\nExample:")
            print("  python copy_trained_models.py C:/path/to/trained/models")
            print("\nNote: The source directory should contain:")
            for model_file in MODEL_FILES:
                print(f"  - {model_file}")

    # Verify models after copying
    print("\n" + "=" * 60)
    verify_models()
