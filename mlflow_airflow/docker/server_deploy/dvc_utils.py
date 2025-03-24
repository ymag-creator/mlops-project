import os
import shutil
import subprocess
import os
import time
# import random


def ensure_folder(folder_path):
    """Create folder if necessary"""
    if os.path.exists(folder_path) == False:
        os.makedirs(folder_path, exist_ok=True)

def copy_files(input_dir, output_dir):
    # Déplace les fichers de raw_to_ingest dans raw_ingested
    # Parcourir tous les fichiers dans le dossier source
    for filename in os.listdir(input_dir):
        src_path = os.path.join(input_dir, filename)
        dst_path = os.path.join(output_dir, filename)
        if os.path.isfile(src_path):  # On ne déplace que les fichiers
            shutil.copy(src_path, dst_path)


def dvc_push(branche, version):
    """
    Force l'envoi des répertoires spécifiés vers DVC, crée un tag et pousse vers DagsHub et GitHub.

    Args:
        repo_url (str): URL du dépôt GitHub.
        repo_path (str): Chemin local du dépôt Git/DVC.
        directories (list): Liste des chemins des répertoires à forcer l'envoi.
        tag_name (str): Nom du tag DVC à créer.
        github_username (str): Nom d'utilisateur GitHub.
        github_password (str): Mot de passe GitHub ou jeton d'accès personnel.
        dagshub_username (str): Nom d'utilisateur DagsHub.
        dagshub_password (str): Mot de passe DagsHub ou jeton d'accès personnel.
    """

    repo_path = "/app/repo_git"
    directories = ["data/processed_trained", "data/raw_ingested"]
    directories_source = ["/app/data_to_push/processed_trained", "/app/data_to_push/raw_ingested"]
    tag_name = f"model-version-v{version}"  # str(random.randint(10000, 101000000))
    github_url = "https://LordBelasco:{token}@github.com/LordBelasco/Projet_MLOps_accidents.git"
    # dagshub_url = "https://lordbelasco:token@dagshub.com/lordbelasco/Projet_MLOps_accidents.s3"

    # --- 1. Cloner le dépôt avec authentification ---
    # On injecte le token dans l'URL pour éviter le prompt
    print("clone")
    subprocess.run(
        ["git", "clone", "--branch", branche, github_url, repo_path],
        check=True,
    )

    os.chdir(repo_path)

    try:

        # Coppie les données à pousser à partir du mount sur data vers le repo git
        for i in range(0, len(directories)):
            dest = repo_path + "/" + directories[i]
            ensure_folder(dest)
            copy_files(directories_source[i], dest)

        # Configurer Git, sinon il y a une erreur
        subprocess.run(
            ["git", "config", "user.name", "build"],
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "build@build.fr"],
            check=True,
        )

        # Ajoute la config du repo dagshub dans dvc local, pour que le push fonctionne
        print("Config DVC local pour access_key")
        subprocess.run(
            [
                "dvc",
                "remote",
                "modify",
                "origin",
                "--local",
                "access_key_id",
                "token",
            ],
            check=True,
        )
        subprocess.run(
            [
                "dvc",
                "remote",
                "modify",
                "origin",
                "--local",
                "secret_access_key",
                "token",
            ],
            check=True,
        )

        # Force l'ajout des répertoires de données dans dvc et les .dvc dans git
        print("add des fichiers")
        for d in directories:
            try:
                # Ajouter/mettre à jour le tracking DVC (même s’il n’a pas changé)
                subprocess.run(
                    ["dvc", "add", d],
                    check=True,
                )
                # Ajouter le fichier .dvc généré dans Git
                subprocess.run(
                    ["git", "add", f"{d}.dvc"],
                    check=True,
                )
            except:
                pass

        # dvc commit
        print("dvc commit")
        subprocess.run(
            ["dvc", "commit", "-v"],
            check=False,
        )
        # git commit
        print("git commit")
        subprocess.run(
            ["git", "commit", "-m", f"Maj données Model {tag_name}"],
            check=False,
        )

        # Pousser les données DVC vers DagsHub
        print("dvc push")
        subprocess.run(
            ["dvc", "push", "-v"], check=True
        )

        # Pousse les commits Git vers GitHub
        print("git push")
        subprocess.run(
            ["git", "push", "origin", branche],
            check=True,
        )

        # Crée et pousse un tag Git
        print("git tag")
        subprocess.run(
            ["git", "tag", tag_name],
            check=True
        )
        print("git push tag")
        subprocess.run(
            ["git", "push", "origin", tag_name],
            check=True
        )

        print(f"Maj des données github/dagshub: {tag_name}")

    except:
        pass

    os.chdir("/app")


# try:
#     # Clonage du dépôt
#     git.Repo.clone_from(github_url, repo_path)

#     # Configuration du répertoire de travail
#     os.chdir(repo_path)

#     # Force l'ajout et l'envoi des répertoires DVC
#     for directory in directories:
#         subprocess.run(["dvc", "add", directory], check=True)
#     # Ajout, commit et push vers GitHub
#     subprocess.run(["git", "add", "."], check=True)


#     dvc commit
#     subprocess.run(["dvc", "push", "--force"], check=True)

#     git add

#     git commit

#     dvc push
#     git push

#     subprocess.run(["dvc", "push", "--force"], check=True)

#     # Création du tag DVC
#     subprocess.run(["dvc", "tag", tag_name, "--force"], check=True)


#     subprocess.run(
#         ["git", "commit", "-m", f"Force push DVC data and tag {tag_name}"],
#         check=True,
#     )
#     subprocess.run(
#         [
#             "git",
#             "push",
#             github_url,
#             "--force",
#         ],
#         check=True,
#     )

#     # Push vers DagsHub (si nécessaire)
#     subprocess.run(
#         [
#             "git",
#             "remote",
#             "add",
#             "dagshub",
#             dagshub_url,
#         ],
#         check=True,
#     )
#     subprocess.run(["git", "push", "dagshub", "--force"], check=True)

#     print(
#         f"Répertoires forcés, tag '{tag_name}' créé et push vers GitHub et DagsHub réussi."
#     )

# except subprocess.CalledProcessError as e:
#     print(f"Erreur: {e}")
# except git.GitCommandError as e:
#     print(f"Erreur Git: {e}")
# except Exception as e:
#     print(f"Erreur: {e}")

# os.chdir("/app")
