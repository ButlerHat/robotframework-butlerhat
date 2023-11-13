from fastapi.testclient import TestClient
from app import app  # Assuming your FastAPI app is in a file named 'main.py'
from unittest.mock import patch, MagicMock
from data_types.kubernetes_manager import KubernetesManager
from data_types.browser_instance import BrowserInstance

client = TestClient(app)

def test_create_browser():
    test_browser_instance = BrowserInstance(
        id_="test_name",
        deployment_manifest={"deployment": "details"},
        service_manifest={"service": "details"}
    )

    # Mocking the static methods and properties used in the __post_init__ method
    # KubernetesManager.get_endpoint = MagicMock(side_effect=lambda name, service: f"{name}_{service}")

    with patch('orchestrator_manager.OrchestratorManager.create_browser_instance', return_value=test_browser_instance):
        response = client.get("/create-browser")
        assert response.status_code == 200
        assert response.json() == {
            "name": "test_name",
            "playwright_endpoint": f"ws://{KubernetesManager.cloudflare_tunnel}/test_name_playwright",
            "novnc_endpoint": f"http://{KubernetesManager.cloudflare_tunnel}/test_name_novnc/vnc.html?path=test_name_novnc/websockify"
        }

def test_destroy_browser():
    with patch('orchestrator_manager.OrchestratorManager.delete_browser_instance', return_value=None):
        response = client.delete("/destroy-browser/test_name")
        assert response.status_code == 204

