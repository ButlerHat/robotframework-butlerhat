import os
import uuid
import yaml
from typing import Dict, Optional
from data_types.kubernetes_manager import KubernetesManager
from data_types.browser_instance import BrowserInstance

class OrchestratorManager:
    """
    Manages browser instances and their lifecycle using KubernetesManager.

    Attributes:
        browsers (Dict[str, BrowserInstance]): Dictionary that maps the instance id_ 
                                               to its BrowserInstance object.
        k8s_manager (KubernetesManager): Instance of KubernetesManager to handle Kubernetes operations.
    """
    orchestrator_file_path = "orchestrator.yaml"

    def __init__(self):
        self.browsers: Dict[str, BrowserInstance] = {}
        self.k8s_manager: KubernetesManager = KubernetesManager()

        if os.path.exists(self.orchestrator_file_path):
            with open(self.orchestrator_file_path, "r") as f:
                self_dict = yaml.safe_load(f.read())
                self.browsers = {id_: BrowserInstance.from_dict(browser) for id_, browser in self_dict["browsers"].items()}

        try:
            self.k8s_manager.init_ingress()
        except Exception as e:
            print(f"Warn: Failed to initialize ingress. Maybe already created: {e}")
        finally:
            self.k8s_manager.wait_for_ingress_ready()

        # Delete deployments that are not in the orchestrator file
        for deployment_name in self.k8s_manager.get_deployments_in_namespace():
            if 'chrome-' in deployment_name and deployment_name.replace('chrome-', "") not in self.browsers:
                try:
                    self.k8s_manager.delete_chrome_browser(deployment_name.replace('chrome-', ""))
                except Exception as e:
                    print(f"Warn: Failed to delete deployment {deployment_name}: {e}")

    def create_browser_instance(self) -> Optional[BrowserInstance]:
        """
        Creates a new browser instance and adds it to the browser dictionary.

        Returns:
            BrowserInstance: The created browser instance or None if it could not be created.

        Raises:
            ApiException: If the Kubernetes API call fails.
        """
        # Generate unique id
        id_: str = str(uuid.uuid4())
        deployment, service = self.k8s_manager.deploy_chrome_browser(id_)

        browser_instance = BrowserInstance(
            id_=id_,
            deployment_manifest=deployment,
            service_manifest=service
        )

        self.browsers[id_] = browser_instance
        self.save_to_file()
        return browser_instance
        
    def delete_browser_instance(self, id_: str) -> None:
        """
        Deletes an existing browser instance.

        Args:
            id_ (str): Identifier of the browser to delete.

        Raises:
            ValueError: If the browser instance does not exist.
            ApiException: If the Kubernetes API call fails.

        """
        if id_ in self.browsers:
            self.k8s_manager.delete_chrome_browser(id_)
            del self.browsers[id_]
            self.save_to_file()
        else:
            raise ValueError(f"Browser instance {id_} does not exist")

    def stop(self):
        """
        Stops the orchestrator gracefully.
        """
        for id_ in self.browsers.keys():
            self.k8s_manager.delete_chrome_browser(id_)

        self.save_to_file()
        self.k8s_manager.delete_ingress()

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the orchestrator.

        Returns:
            dict: Dictionary representation of the orchestrator.
        """
        return {
            "browsers": {id_: browser.to_dict() for id_, browser in self.browsers.items()}
        }
    
    def to_yaml(self) -> str:
        """
        Returns a YAML representation of the orchestrator.

        Returns:
            str: YAML representation of the orchestrator.
        """
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OrchestratorManager':
        """
        Creates an OrchestratorManager from a dictionary.

        Args:
            data (dict): Dictionary with the orchestrator data.

        Returns:
            OrchestratorManager: OrchestratorManager created from the dictionary.
        """
        orchestrator = cls()
        orchestrator.browsers = {id_: BrowserInstance.from_dict(browser) for id_, browser in data["browsers"].items()}
        return orchestrator
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'OrchestratorManager':
        """
        Creates an OrchestratorManager from a YAML string.

        Args:
            yaml_str (str): YAML string with the orchestrator data.

        Returns:
            OrchestratorManager: OrchestratorManager created from the YAML string.
        """
        return cls.from_dict(yaml.safe_load(yaml_str))
    
    def save_to_file(self, file_path: str | None = None) -> None:
        """
        Saves the orchestrator to a file.

        Args:
            file_path (str): Path to the file where the orchestrator will be saved.
        """
        if file_path is None:
            file_path = self.orchestrator_file_path
        with open(file_path, "w") as f:
            f.write(self.to_yaml())

        