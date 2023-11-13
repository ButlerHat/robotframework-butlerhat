import yaml
from dataclasses import dataclass, field
from data_types.kubernetes_manager import KubernetesManager

@dataclass
class BrowserInstance:
    """
    Represents an instance of a browser in the orchestration system.

    Attributes:
        id_ (str): Unique identifier of the browser.
        playwright_endpoint (str): Endpoint for Playwright.
        novnc_endpoint (str): Endpoint for noVNC.
        novnc_pass (str): Password for noVNC.
    """

    id_: str
    deployment_manifest: dict
    service_manifest: dict
    novnc_pass: str = field(default='vscode', init=False)
    playwright_endpoint: str = field(default= KubernetesManager.cloudflare_tunnel, init=False)
    novnc_endpoint: str = field(default= KubernetesManager.cloudflare_tunnel, init=False)

    def __post_init__(self):
        """
        Validates the data after the instance initialization.
        """
        
        if self.playwright_endpoint == KubernetesManager.cloudflare_tunnel:
            self.playwright_endpoint = f"ws://{KubernetesManager.cloudflare_tunnel}/{KubernetesManager.get_endpoint(self.id_, 'playwright')}/ws"
        if self.novnc_endpoint == KubernetesManager.cloudflare_tunnel:
            no_vnc_endpoint = KubernetesManager.get_endpoint(self.id_, 'novnc')
            self.novnc_endpoint = f"https://{KubernetesManager.cloudflare_tunnel}/{no_vnc_endpoint}/vnc.html" + \
                f"?path={no_vnc_endpoint}/websockify"

        # Here you can add specific validations if you need
        if not self.playwright_endpoint.startswith("ws://"):
            raise ValueError("The Playwright endpoint must start with 'ws://'")
        if not self.novnc_endpoint.startswith("http://") and not self.novnc_endpoint.startswith("https://"):
            raise ValueError("The noVNC endpoint must start with 'http://'")
        
    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the browser instance.

        Returns:
            dict: Dictionary representation of the browser instance.
        """
        return {
            "id_": self.id_,
            "deployment_manifest": self.deployment_manifest,
            "service_manifest": self.service_manifest,
            "playwright_endpoint": self.playwright_endpoint,
            "novnc_endpoint": self.novnc_endpoint,
            "novnc_pass": self.novnc_pass
        }
    
    def to_yaml(self) -> str:
        """
        Returns a YAML representation of the browser instance.

        Returns:
            str: YAML representation of the browser instance.
        """
        return yaml.dump(self.to_dict(), default_flow_style=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BrowserInstance':
        """
        Creates a BrowserInstance from a dictionary.

        Args:
            data (dict): Dictionary with the browser instance data.

        Returns:
            BrowserInstance: BrowserInstance created from the dictionary.
        """
        return cls(
            id_=data["id_"],
            deployment_manifest=data["deployment_manifest"],
            service_manifest=data["service_manifest"]
        )
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'BrowserInstance':
        """
        Creates a BrowserInstance from a YAML string.

        Args:
            yaml_str (str): YAML string with the browser instance data.

        Returns:
            BrowserInstance: BrowserInstance created from the YAML string.
        """
        return cls.from_dict(yaml.safe_load(yaml_str))
        