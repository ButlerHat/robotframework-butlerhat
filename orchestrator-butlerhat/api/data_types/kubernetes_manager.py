import os
import yaml
import time
from typing import Any, Literal
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

class KubernetesManager:
    """
    This class manages the Kubernetes.
    """
    cloudflare_tunnel: str = "k8-chrome.paipaya.com"

    def __init__(self):
        # Carga la configuración de Kubernetes. 
        # Esto se ajustará dependiendo del entorno (p.ej., local, EKS, GKE)
        config.load_kube_config()

        self.apps_v1_api = client.AppsV1Api()
        self.core_v1_api = client.CoreV1Api()
        self.networking_v1_api = client.NetworkingV1Api()
        
        # Nombres de los recursos
        self.deployment_name = "chrome-{instance_id}"
        self.service_name = "service-chrome-{instance_id}"
        self.ingress_name = "ingress-chrome"
        self.namespace = "default"

        # Ports
        self.playwright_port = 4445
        self.novnc_port = 6080

        # Manifests
        current_dir = os.path.dirname(__file__)
        manifest_dir = os.path.join(current_dir, 'manifests')

        self.deployment_manifest_path = os.path.join(manifest_dir, "chrome_deployment.yml")
        self.service_manifest_path = os.path.join(manifest_dir, "chrome_service.yml")
        self.ingress_manifest_path = os.path.join(manifest_dir, "ingress.yml")
        self.cloudflare_manifest_path = os.path.join(manifest_dir, "cloudflare_deployment.yml")

    def _create_deployment(self, deployment_manifest: dict):
        """
        This method creates a new deployment in Kubernetes using the provided deployment manifest.

        Args:
            deployment_manifest (dict): The deployment manifest as a dictionary.

        Raises:
            ApiException: If there is an error from the Kubernetes API.
        """
        try:
            self.apps_v1_api.create_namespaced_deployment(
                namespace=self.namespace, body=deployment_manifest)
        except ApiException as e:
            raise ApiException(f"Exception when calling AppsV1Api->create_namespaced_deployment: {e}")

    def _create_service(self, service_manifest: dict):
        """
        This method creates a new service in Kubernetes using the provided service manifest.

        Args:
            service_manifest (dict): The service manifest as a dictionary.

        Raises:
            ApiException: If there is an error from the Kubernetes API.
        """
        try:
            self.core_v1_api.create_namespaced_service(
                namespace=self.namespace, body=service_manifest)
        except ApiException as e:
            raise ApiException(f"Exception when calling CoreV1Api->create_namespaced_service: {e}")

    def _delete_deployment(self, name: str, namespace: str | None = None):
        """
        Deletes a deployment with the given name in the specified namespace.

        Args:
            name (str): The name of the deployment to delete.
            namespace (str, optional): The namespace in which the deployment is located. Defaults to None.

        Raises:
            ApiException: If there was an error deleting the deployment.

        """
        if namespace is None:
            namespace = self.namespace

        try:
            self.apps_v1_api.delete_namespaced_deployment(
                name=name, namespace=namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling AppsV1Api->delete_namespaced_deployment: {e}")

    def _delete_service(self, name: str, namespace: str | None = None):
        """
        Deletes an existing Kubernetes service.

        Args:
            name (str): The name of the service to delete.
            namespace (str, optional): The namespace of the service. Defaults to None.
        """
        if namespace is None:
            namespace = self.namespace

        try:
            self.core_v1_api.delete_namespaced_service(
                name=name, namespace=namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling CoreV1Api->delete_namespaced_service: {e}")

    def _add_ingress_rule(self, instance_id: str):
        """
        This method adds new ingress rules for the specified chrome in Kubernetes. It assumes that the ingress already exists.

        Args:
            instance_id (str): The ID of the instance for which the ingress rules are to be added.

        Raises:
            ApiException: If there is an error from the Kubernetes API.
        """
        service_name = self.service_name.format(instance_id=instance_id)

        # Carga el Ingress existente
        try:
            ingress = self.networking_v1_api.read_namespaced_ingress(self.ingress_name, self.namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->read_namespaced_ingress: {e}")

        # Construye nuevas reglas
        new_playwright_rule = {
            'path': f"/{self.get_endpoint(instance_id, 'playwright')}(/|$)(.*)",
            'pathType': "ImplementationSpecific",
            'backend': {
                'service': {
                    'name': service_name,
                    'port': {
                        'number': self.playwright_port
                    }
                }
            }
        }

        new_novnc_rule = {
            'path': f"/{self.get_endpoint(instance_id, 'novnc')}(/|$)(.*)",
            'pathType': "ImplementationSpecific",
            'backend': {
                'service': {
                    'name': service_name,
                    'port': {
                        'number': self.novnc_port
                    }
                }
            }
        }

        # Agrega las nuevas reglas al Ingress
        assert isinstance(ingress, client.V1Ingress)
        if ingress.spec is None:
            ingress.spec = client.V1IngressSpec()
        if ingress.spec.rules is None:
            ingress.spec.rules = []
        for rule in ingress.spec.rules:
            if hasattr(rule, 'http') and rule.http is not None:
                rule.http.paths.append(new_playwright_rule)
                rule.http.paths.append(new_novnc_rule)
                break
        else:
            ingress.spec.rules.append(client.V1IngressRule(http=client.V1HTTPIngressRuleValue(paths=[
                new_playwright_rule,
                new_novnc_rule
            ])))
            
        # Actualiza el Ingress en Kubernetes
        try:
            self.networking_v1_api.replace_namespaced_ingress(
                self.ingress_name, 
                self.namespace, 
                ingress
            )
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->replace_namespaced_ingress: {e}")

    def _delete_ingress_rule(self, instance_id: str):
        """
        This method deletes ingress rules for the specified instance in Kubernetes.

        Args:
            instance_id (str): The ID of the instance for which the ingress rules are to be deleted.

        Raises:
            ApiException: If there is an error from the Kubernetes API.
        """
        # Carga el Ingress existente
        try:
            ingress = self.networking_v1_api.read_namespaced_ingress(self.ingress_name, self.namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->read_namespaced_ingress: {e}")

        # Elimina las reglas para la instancia
        assert isinstance(ingress, client.V1Ingress)
        if ingress.spec is None:
            print("Ingress doesn't have a spec. Not deleting any rules.")
            return
        if ingress.spec.rules is None:
            print("Ingress doesn't have any rules. Not deleting any rules.")
            return
        rule_found = False
        for rule in ingress.spec.rules:
            if hasattr(rule, 'http') and rule.http is not None:
                to_remove = []
                for ingress_path in rule.http.paths:
                    path = ingress_path.path
                    if f"_{instance_id}" in path:
                        to_remove.append(ingress_path)
                        rule_found = True
                for ingress_path in to_remove:
                    rule.http.paths.remove(ingress_path)
                if len(rule.http.paths) == 0:
                    ingress.spec.rules.remove(rule)
        if not rule_found:
            raise Exception(f"No rule found for instance {instance_id}")
        
        # Actualiza el Ingress en Kubernetes
        try:
            self.networking_v1_api.replace_namespaced_ingress(
                self.ingress_name, 
                self.namespace, 
                ingress
            )
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->replace_namespaced_ingress: {e}")

    @staticmethod
    def get_endpoint(instance_id: str, endpoint_type: Literal['playwright', 'novnc']) -> str:
        """
        Gets the endpoint for the specified instance and endpoint type.

        Args:
            instance_id (str): The ID of the instance.
            endpoint_type (str): The type of endpoint to get. Can be either 'playwright' or 'novnc'.

        Returns:
            str: The endpoint URL.
        """
        if endpoint_type == 'playwright':
            return f"playwright_{instance_id}"
        elif endpoint_type == 'novnc':
            return f"novnc_{instance_id}"
        else:
            raise ValueError(f"Invalid endpoint type: {endpoint_type}")

    def init_ingress(self):
        """
        Deploy the Ingress and Cloudflare Tunnel
        """
        # Create the Ingress
        with open(self.ingress_manifest_path, 'r') as file:
            ingress_manifest = yaml.safe_load(file)
        try:
            self.networking_v1_api.create_namespaced_ingress(
                namespace=self.namespace, body=ingress_manifest)
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->create_namespaced_ingress: {e}")

        # Create the Cloudflare Tunnel
        with open(self.cloudflare_manifest_path, 'r') as file:
            cloudflare_manifest = yaml.safe_load(file)
        try:
            self.apps_v1_api.create_namespaced_deployment(
                namespace=self.namespace, body=cloudflare_manifest)
        except ApiException as e:
            raise ApiException(f"Exception when calling AppsV1Api->create_namespaced_deployment: {e}")

    def get_deployments_in_namespace(self) -> list[str]:
        """
        Returns a list of all deployments in the namespace.

        Returns:
            list[str]: A list of all deployments in the namespace.
        """
        try:
            deployments = self.apps_v1_api.list_namespaced_deployment(
                namespace=self.namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling AppsV1Api->list_namespaced_deployment: {e}")

        return [deployment.metadata.name for deployment in deployments.items]

    def delete_ingress(self):
        """
        Stop the Ingress and Cloudflare Tunnel
        """
        # Delete the Ingress
        try:
            self.networking_v1_api.delete_namespaced_ingress(
                name=self.ingress_name, namespace=self.namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling NetworkingV1Api->delete_namespaced_ingress: {e}")

        # Delete the Cloudflare Tunnel
        with open(self.cloudflare_manifest_path, 'r') as file:
            cloudflare_manifest = yaml.safe_load(file)
        cloudflare_name = cloudflare_manifest['metadata']['name']
        try:
            self.apps_v1_api.delete_namespaced_deployment(
                name=cloudflare_name, namespace=self.namespace)
        except ApiException as e:
            raise ApiException(f"Exception when calling AppsV1Api->delete_namespaced_deployment: {e}")
    
    def wait_for_deployment_ready(self, instance_id: str, timeout: int = 300) -> bool:
        """
        Waits for a Kubernetes deployment to be ready.

        Args:
            instance_id (str): The ID of the deployment instance.
            timeout (int, optional): The maximum time to wait for the deployment to be ready, in seconds. Defaults to 300.

        Returns:
            bool: True if the deployment is ready, False otherwise.
        """
        deployment_name = self.deployment_name.format(instance_id=instance_id)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                deployment = self.apps_v1_api.read_namespaced_deployment(deployment_name, self.namespace)
                if isinstance(deployment, client.V1Deployment) \
                and deployment.status \
                and deployment.status.available_replicas == deployment.status.replicas:
                    print(f"Deployment {deployment_name} is ready.")
                    return True
            except ApiException as e:
                print(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}")
                return False

            print(f"Waiting for deployment {deployment_name} to be ready...")
            time.sleep(10)  # Wait for 10 seconds before the next check

        print(f"Timeout reached: Deployment {deployment_name} is not ready.")
        return False
    
    def wait_for_ingress_ready(self, timeout: int = 300) -> bool:
        """
        Waits for the ingress to be ready for the specified amount of time.

        Args:
            timeout (int): The maximum amount of time to wait for the ingress to be ready, in seconds.

        Returns:
            bool: True if the ingress is ready within the specified timeout, False otherwise.
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                ingress = self.networking_v1_api.read_namespaced_ingress(self.ingress_name, self.namespace)
                if isinstance(ingress, client.V1Ingress) \
                and ingress.status \
                and ingress.status.load_balancer \
                and ingress.status.load_balancer.ingress:
                    print(f"Ingress {self.ingress_name} is ready.")
                    return True
            except ApiException as e:
                print(f"Exception when calling NetworkingV1Api->read_namespaced_ingress: {e}")
                return False

            print(f"Waiting for ingress {self.ingress_name} to be ready...")
            time.sleep(10)

        print(f"Timeout reached: Ingress {self.ingress_name} is not ready.")
        return False

    def is_browser_running(self, instance_id: str):
        """
        Checks if the browser deployment and service are running for the given instance ID.

        Args:
            instance_id (str): The ID of the instance to check.

        Returns:
            bool: True if the deployment and service are running, False otherwise.
        """
        deployment_name = self.deployment_name.format(instance_id=instance_id)
        service_name = self.service_name.format(instance_id=instance_id)

        # Check the deployment status
        try:
            deployment: client.V1Deployment | Any = self.apps_v1_api.read_namespaced_deployment(deployment_name, self.namespace)
            if not isinstance(deployment, client.V1Deployment) \
                or not deployment.status \
                or not deployment.status.available_replicas:
                return False
        except ApiException as e:
            print(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}")
            return False

        # Check the service status
        try:
            service = self.core_v1_api.read_namespaced_service(service_name, self.namespace)
            # Service doesn't have a 'running' status per se, so we check if it exists
            if not service:
                return False
        except ApiException as e:
            print(f"Exception when calling CoreV1Api->read_namespaced_service: {e}")
            return False

        # Both deployment and service exist and deployment has available replicas
        return True

    def deploy_chrome_browser(self, instance_id: str) -> tuple[dict, dict]:
        """
        This method deploys a Chrome browser in Kubernetes for the specified instance.
        Also waits for the deployment to be ready.

        Args:
            instance_id (str): The ID of the instance for which the Chrome browser is to be deployed.

        Returns:
            tuple[dict, dict]: The deployment and service manifests as dictionaries.

        Raises:
            ApiException: If there is an error from the Kubernetes API.
        """
        deployment_name = self.deployment_name.format(instance_id=instance_id)
        service_name = self.service_name.format(instance_id=instance_id)

        # Cargar y modificar el manifiesto del deployment
        with open(self.deployment_manifest_path, 'r') as file:
            deployment_manifest = yaml.safe_load(file)

        # Actualizar el nombre y las etiquetas del deployment
        deployment_manifest['metadata']['name'] = deployment_name
        deployment_manifest['spec']['selector']['matchLabels']['app'] = deployment_name
        deployment_manifest['spec']['template']['metadata']['labels']['app'] = deployment_name

        # Actualizar los puertos
        for container in deployment_manifest['spec']['template']['spec']['containers']:
            if container['name'] == 'chrome-playwright-container':
                for port in container['ports']:
                    if port['name'] == 'playwright':
                        port['containerPort'] = self.playwright_port
                    elif port['name'] == 'novnc':
                        port['containerPort'] = self.novnc_port

        # Crear el deployment en Kubernetes
        self._create_deployment(deployment_manifest)

        # Cargar y modificar el manifiesto del servicio
        with open(self.service_manifest_path, 'r') as file:
            service_manifest = yaml.safe_load(file)

        # Actualizar el nombre y selector del servicio
        service_manifest['metadata']['name'] = service_name
        service_manifest['spec']['selector']['app'] = deployment_name

        # Actualizar los puertos
        for port in service_manifest['spec']['ports']:
            if port['name'] == 'playwright':
                port['port'] = self.playwright_port
                port['targetPort'] = self.playwright_port
            elif port['name'] == 'novnc':
                port['port'] = self.novnc_port
                port['targetPort'] = self.novnc_port

        # Crear el servicio en Kubernetes
        try:
            self.core_v1_api.create_namespaced_service(
                namespace=self.namespace, body=service_manifest)
        except ApiException as e:
            raise Exception(f"Exception when calling CoreV1Api->create_namespaced_service: {e}")

        # Actualizar el Ingress
        self.wait_for_deployment_ready(instance_id)
        self._add_ingress_rule(instance_id)
        
        return deployment_manifest, service_manifest
    
    def delete_chrome_browser(self, instance_id: str):
            """
            Deletes the deployment, service, and ingress rule for the Chrome browser instance with the given ID.

            Args:
                instance_id (str): The ID of the Chrome browser instance to delete.
            """
            deployment_name = self.deployment_name.format(instance_id=instance_id)
            service_name = self.service_name.format(instance_id=instance_id)

            self._delete_deployment(deployment_name)
            self._delete_service(service_name)
            self._delete_ingress_rule(instance_id)

if __name__ == '__main__':
    k8s_manager = KubernetesManager()
    k8s_manager.init_ingress()
    print('Waiting for ingress to be ready...')
    k8s_manager.wait_for_ingress_ready()
    print('Ingress is ready!')
    deployment_manifest, service_manifest = k8s_manager.deploy_chrome_browser('test-instance')
    print('Waiting for deployment to be ready...')
    k8s_manager.wait_for_deployment_ready('test-instance')
    print('Deployment is ready!')
    print(k8s_manager.is_browser_running('test-instance'))

    # Second deployment
    deployment_manifest, service_manifest = k8s_manager.deploy_chrome_browser('test-instance2')
    print('2 Waiting for deployment to be ready...')
    k8s_manager.wait_for_deployment_ready('test-instance2')
    print('2 Deployment is ready!')
    print(k8s_manager.is_browser_running('test-instance2'))


    k8s_manager.delete_chrome_browser('test-instance')
    print('Deployment deleted!')
    k8s_manager.delete_chrome_browser('test-instance2')
    print('Deployment deleted!')
    
    k8s_manager.delete_ingress()
    print('Ingress deleted!')