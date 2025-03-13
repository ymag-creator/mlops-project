import os
from pathlib import Path
import shutil

def check_existing_file(file_path):
    '''Check if a file already exists. If it does, ask if we want to overwrite it.'''
    if os.path.isfile(file_path):
        while True:
            response = input(f"File {os.path.basename(file_path)} already exists. Do you want to overwrite it? (y/n): ")
            if response.lower() == 'y':
                return True
            elif response.lower() == 'n':
                return False
            else:
                print("Invalid response. Please enter 'y' or 'n'.")
    else:
        return True


def ensure_folder(folder_path):
    """ Create folder if necessary"""
    if os.path.exists(folder_path) == False :
        os.makedirs(folder_path, exist_ok=True)

def delete_files(folder_path):
    repertoire = Path(folder_path)
    for fichier in repertoire.iterdir():
        if fichier.is_file():
            fichier.unlink()

def move_files(input_dir, output_dir):
    # Déplace les fichers de raw_to_ingest dans raw_ingested
    # Parcourir tous les fichiers dans le dossier source
    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)
        if os.path.isfile(src_path):  # On ne déplace que les fichiers
            shutil.move(src_path, dst_path)
