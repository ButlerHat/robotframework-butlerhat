import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_types'))
from data_types.kubernetes_manager import KubernetesManager  

class TestKubernetesManager(unittest.TestCase):
    instance_id = 'test-instance'

    def setUp(self):
        self.k8s_manager = KubernetesManager()

    def test_deploy_chrome_browser(self):
        # Llamar al método deploy_chrome_browser
        # Nota: esta llamada ahora realmente intentará desplegar en Kubernetes si tienes un entorno configurado
        deployment_manifest, service_manifest = self.k8s_manager.deploy_chrome_browser(TestKubernetesManager.instance_id)

        # Verificar que los manifiestos fueron creados correctamente
        self.assertEqual(deployment_manifest['metadata']['name'], f'chrome-{TestKubernetesManager.instance_id}')
        self.assertEqual(deployment_manifest['spec']['selector']['matchLabels']['app'], f'chrome-{TestKubernetesManager.instance_id}')
        self.assertEqual(deployment_manifest['spec']['template']['metadata']['labels']['app'], f'chrome-{TestKubernetesManager.instance_id}')

        self.assertEqual(service_manifest['metadata']['name'], f'service-chrome-{TestKubernetesManager.instance_id}')
        self.assertEqual(service_manifest['spec']['selector']['app'], f'chrome-{TestKubernetesManager.instance_id}')

        # Verify that the deployment and service were created. Wait until they are ready
        self.k8s_manager.wait_for_deployment_ready(TestKubernetesManager.instance_id)

        # Verify that the deployment and service exist
        self.assertTrue(self.k8s_manager.is_browser_running(TestKubernetesManager.instance_id))

        # Delete the deployment and service
        self.k8s_manager.delete_chrome_browser(TestKubernetesManager.instance_id)

    def tearDown(self) -> None:
        # Eliminar los despliegues y servicios creados
        self.k8s_manager.delete_chrome_browser(TestKubernetesManager.instance_id)


if __name__ == '__main__':
    unittest.main()
