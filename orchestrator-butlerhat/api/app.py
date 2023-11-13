from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from data_types.orchestrator_manager import OrchestratorManager

app = FastAPI()
orchestrator = OrchestratorManager()

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Logic to be executed before the application starts
    yield
    # Logic to be executed when the application is shutting down
    # orchestrator.stop()

app = FastAPI(lifespan=app_lifespan)

class BrowserCreationResponse(BaseModel):
    id_: str
    playwright_endpoint: str
    novnc_endpoint: str

@app.get("/create-browser", response_model=BrowserCreationResponse)
def create_browser():
    try:
        browser_instance = orchestrator.create_browser_instance()
        if browser_instance:
            return BrowserCreationResponse(
                id_=browser_instance.id_,
                playwright_endpoint=browser_instance.playwright_endpoint,
                novnc_endpoint=browser_instance.novnc_endpoint
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create browser instance")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/destroy-browser/{id_}", status_code=204)
def destroy_browser(id_: str):
    try:
        orchestrator.delete_browser_instance(id_)
    except ValueError:
        raise HTTPException(status_code=404, detail="Browser instance not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0")   # type: ignore