from kubernetes.utils import create_from_yaml
from kubernetes import client, config, utils
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
import yaml
import os
import time


class TestError(Exception):
    pass


# Charge automatiquement ~/.kube/config (monté depuis le host dans le container)
config.load_kube_config()

# lister les pods pour vérifier la connexion
core_api = client.CoreV1Api()
print("Listing pods in all namespaces:")
pods = core_api.list_pod_for_all_namespaces()
for pod in pods.items:
    print(f"{pod.metadata.namespace}/{pod.metadata.name}")

# chemins
yaml_path = "data/fastapi-test-job.yaml"
namespace = "projet-mlops"
job_name = "fastapi-tests"
pv_name = "fastapi-tests"
pvc_name = "fastapi-tests"

batch_api = client.BatchV1Api()

# Créer PV, PVC et Job
create_from_yaml(client.ApiClient(), yaml_path, namespace=namespace)

# Attendre que le Job démarre
print("⏳ En attente de fin du Job...")

try:
    while True:
        job_status = batch_api.read_namespaced_job_status(job_name, namespace)
        if job_status.status.succeeded is not None and job_status.status.succeeded >= 1:            
            break
        elif job_status.status.failed is not None and job_status.status.failed > 0:
            print("❌ Job a échoué.")
            raise TestError("Les tests ont échoué")
        time.sleep(2)
finally:
    # Récupérer le nom du pod
    pods = core_api.list_namespaced_pod(namespace, label_selector=f"job-name={job_name}")
    pod_name = pods.items[0].metadata.name

    # Lire les logs
    print(f"\n📄 Logs du pod {pod_name} :\n")
    logs = core_api.read_namespaced_pod_log(name=pod_name, namespace=namespace)
    print(logs)

    # Lire l'état du pod
    pod_status = core_api.read_namespaced_pod_status(name=pod_name, namespace=namespace)
    # Récupérer l'état du conteneur
    container_status = pod_status.status.container_statuses[0]
    # Vérifier si le conteneur s'est terminé
    if container_status.state.terminated:
        exit_code = container_status.state.terminated.exit_code
    else:
        exit_code = 0
    
    # Supprimer les ressources
    print("\n🧹 Nettoyage : suppression du Job, PVC et PV")
    batch_api.delete_namespaced_job(
        name=job_name,
        namespace=namespace,
        body=client.V1DeleteOptions(propagation_policy="Foreground"),
    )
    core_api.delete_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
    core_api.delete_persistent_volume(name=pv_name)

    # Remonte l'erreur au dag
    if exit_code == 0:
        print("✅ Job terminé avec succès.")
    else:
        print("❌ Job a échoué.")
        raise TestError("Les tests ont échoué")