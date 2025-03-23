import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import time
from mlflow_utils import set_production_alias
from dvc_utils import dvc_push

class DeployError(Exception):
    pass


def kubernetes_apply_yaml():
    # Charge automatiquement ~/.kube/config (monté depuis le host dans le container)
    config.load_kube_config()

    # lister les pods pour vérifier la connexion
    core_api = client.CoreV1Api()
    print("Listing pods in all namespaces:")
    pods = core_api.list_pod_for_all_namespaces()
    for pod in pods.items:
        print(f"{pod.metadata.namespace}/{pod.metadata.name}")

    # chemins
    yaml_path = "data/fastapi-deployment.yaml"
    namespace = "projet-mlops"

    apps_api = client.AppsV1Api()

    with open(yaml_path, "r") as f:
        documents = list(yaml.safe_load_all(f))

    # Parcours les items du yaml, car un seul yaml avec deploy, PV et PVC
    # Crée les élements manquants, sinon update, équivalent d'un apply
    for resource in documents:
        if not resource:
            continue
        kind = resource.get("kind")
        metadata = resource.get("metadata", {})
        name = metadata.get("name", "noname")
        print(f"🔧 Traitement de {kind} '{name}'")
        try:

            # -------------- A noter -----------------
            # Vérifier l'existence de chaque ressource, si elle existe, l'update sinon la crée comme le fait
            # Kubectl apply, mais le fait par l'api qui ne semble pas le faire (pas trouvé...)

            # -------------- Deployment -----------------
            if kind == "Deployment":
                # Force le redéploiement des pods même si l'image identique, pour forcer le rechargement du model
                # qui est fait dynamiquement au lancement du server fastapi à partir de MLFlow et du model marqué "En Prod"
                # et si aucune resource du yaml ou image Docker n'a changé, par défaut les pods ne sont pas
                # relancés pour update
                # donc force une modif du yaml après chargement pour forcer un changement et un reload des pods
                resource["spec"]["template"]["metadata"].setdefault("annotations", {})
                resource["spec"]["template"]["metadata"]["annotations"]["force-update"] = str(time.time())
                try:
                    apps_api.read_namespaced_deployment(name, namespace)
                    apps_api.replace_namespaced_deployment(name, namespace, resource)
                    print(f"✅ Deployment '{name}' mis à jour")
                except ApiException as e:
                    print(e)
                    if e.status == 404:
                        apps_api.create_namespaced_deployment(namespace, resource)
                        print(f"✅ Deployment '{name}' créé")
                    else:
                        raise

            # -------------- PersistentVolume -----------------
            elif kind == "PersistentVolume":
                try:
                    core_api.read_persistent_volume(name)
                    # core_api.replace_persistent_volume(name, resource)
                    print(f"✅ PersistentVolume '{name}' mis à jour")
                except ApiException as e:
                    print(e)
                    if e.status == 404:
                        core_api.create_persistent_volume(resource)
                        print(f"✅ PersistentVolume '{name}' créé")
                    else:
                        raise

            # -------------- PersistentVolumeClaim -----------------
            elif kind == "PersistentVolumeClaim":
                try:
                    core_api.read_namespaced_persistent_volume_claim(name, namespace)
                    # core_api.replace_namespaced_persistent_volume_claim(name, namespace, resource)
                    print(f"✅ PVC '{name}' mis à jour")
                except ApiException as e:
                    print(e)
                    if e.status == 404:
                        core_api.create_namespaced_persistent_volume_claim(namespace, resource)
                        print(f"✅ PVC '{name}' créé")
                    # if e.status == 422:
                    #     print(f"✅ PVC '{name}' existante, non modifiée car immutable")
                        
                    # else:
                    #     raise

            # -------------- Service -----------------
            elif kind == "Service":
                try:
                    core_api.read_namespaced_service(name, namespace)
                    core_api.replace_namespaced_service(name, namespace, resource)
                    print(f"🔄 Service '{name}' mis à jour")
                except ApiException as e:
                    print(e)
                    if e.status == 404:
                        core_api.create_namespaced_service(namespace, resource)
                        print(f"✅ Service '{name}' créé")
                    else:
                        raise

            # -------------- non géré -----------------
            else:
                print(f"⚠️ Kind {kind} non géré")
                raise DeployError(f"⚠️ Kind {kind} non géré")

        except ApiException as e:
            print(f"❌ Erreur sur {kind} '{name}': {e.reason}")
            raise

def update_mlflow():
    version = set_production_alias()
    return version


def push_to_dagshub(version):
    dvc_push("Davy", version)


if __name__ == "__main__":
    # kubernetes_apply_yaml()
    # version = update_mlflow()
    # push_to_dagshub(version)
    push_to_dagshub("15")
