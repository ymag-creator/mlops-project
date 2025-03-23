import time
import requests
import pytest
from server_launch import run_server_async


def wait_for_server_ready(url="http://localhost:6100/status", timeout=50):
    print("⏳ Attente du démarrage du serveur...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                print("✅ Serveur prêt !")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("❌ Timeout : le serveur ne répond pas.")
    return False


def start_uvicorn():
    return run_server_async()

import sys
from contextlib import redirect_stdout, redirect_stderr

def run_pytest_and_capture():
    print("🧪 Lancement des tests pytest...")
    with open("data/pytest_output.log", "w") as f:
        sys.stdout = f
        sys.stderr = f
        exit_code = pytest.main(
            [
                "tests.py",  # dossier des tests
                "--capture=tee-sys",  # afficher ET écrire stdout
                "--log-cli-level=DEBUG",  # capture logs niveau INFO+
                "--junitxml=data/results.xml",  # optionnel: résultat XML
            ]
        )
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    # Afficher le contenu du fichier log après exécution
    print("\n📄 Contenu du fichier de log pytest :\n")
    with open("data/pytest_output.log", "r") as f:
        print(f.read())

    # # Ouvre un fichier log pour rediriger stdout + stderr
    # logfile="pytest_output3.log"
    # with open(logfile, "w") as log_file:
    #     with redirect_stdout(log_file), redirect_stderr(log_file):
    #         exit_code = pytest.main(["tests.py"])

    # # Afficher le contenu du fichier log après exécution
    # print("\n📄 Contenu du fichier de log pytest :\n")
    # with open(logfile, "r") as f:
    #     print(f.read())

    # exit_code = pytest.main(
    #     [
    #         "tests.py",  # dossier des tests
    #         "--capture=tee-sys",  # afficher ET écrire stdout
    #         "--junitxml=results.xml",  # optionnel: résultat XML
    #         "--log-file=pytest_output2.log",
    #     ]
    # )
    return exit_code


def main():
    server_process = start_uvicorn()
    try:
        if wait_for_server_ready():
            result = run_pytest_and_capture()
            if result == 0:
                print("✅ Tous les tests sont passés.")
            else:
                print(f"❌ Échec des tests (code={result})")
            return result
        else:
            print("⚠️ Tests non lancés, serveur non prêt.")
            return 5
    finally:
        print("🛑 Arrêt du serveur Uvicorn...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    result = main()
    print("exit code", result)
    exit(result)


# def run_pytest_and_capture():
#     exit_code = pytest.main(
#         [
#             "tests.py",  # dossier des tests
#             "--capture=tee-sys",  # afficher ET écrire stdout
#             "--log-cli-level=INFO",  # capture logs niveau INFO+
#             "--junitxml=results.xml",  # optionnel: résultat XML
#         ]
#     )
#     return exit_code

# if __name__ == "__main__":
#     result = run_pytest_and_capture()
#     if result == 0:
#         print("✅ Tous les tests sont passés.")
#     else:
#         print(f"❌ Échec des tests (code={result})")
#     exit(result)
