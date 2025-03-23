import uvicorn
import subprocess


# --------------- A noter ---------------
# run_server_sync sert pour le lancement en prod, sur le port 6200, donc bloque le thread
# run_server_async sert popur les tests, sur le port 6100, et ne bloque pas le thread pour redonner
#    la main à pytest qui attend que le serveur soit lancé pour lancer les tests
#
# il faut des ports différents pour que les tests puissent être lancés en parallèle de la prod ! 
# Peut passer le port en param à partir de tests_launch si besoin été
# --------------- A noter ---------------


def run_server_sync():
    print("🚀 Démarrage du serveur Uvicorn...")
    config = uvicorn.Config("server:app", port=6300, host="0.0.0.0", log_level="info", reload=True)
    server = uvicorn.Server(config)
    server.run()


def run_server_async():
    print("🚀 Démarrage du serveur Uvicorn...")
    uvicorn_proc = subprocess.Popen(
        [
            "uvicorn",
            "server:app",  # ton module FastAPI (adapter à ton projet)
            "--port",
            "6100",
            "--log-level",
            "info",
        ],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    print("Serveur Uvicorn lancé")
    return uvicorn_proc


if __name__ == "__main__":
    run_server_sync()
    # run_server_async()
