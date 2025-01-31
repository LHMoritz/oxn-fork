from pathlib import Path
from pydantic2ts import generate_typescript_defs

# Configuration
OUTPUT_DIR = Path(".")  # TODO: Change this to the frontend/types directory

def generate_types():
    """Generate TypeScript type definitions from Pydantic models"""
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Define models and their output filenames
    models_config = {
        'experiment': "backend.internal.models.experiment",
        # If you add more models, add them here in format: 'output_filename': [Model1, Model2, ...]
    }
    
    for output_name, model_imports in models_config.items():
        output_file = OUTPUT_DIR / f"{output_name}.ts"
        
        try:
            print(f"Generating TypeScript types for {output_name}")
            generate_typescript_defs(
                module=model_imports,
                output=str(output_file),
            )
        except Exception as e:
            print(f"Error generating types for {output_name}: {e}")

if __name__ == "__main__":
    generate_types()