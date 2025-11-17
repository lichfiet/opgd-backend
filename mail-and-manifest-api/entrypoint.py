import logging

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import uvicorn

import routes 

#
# Configure logging
# 
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


#
# FastAPI App
#
server = FastAPI(
    title="OPGD Mail and Manifest API",
    access_log=True
    )

server.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cet.lightspeeddev.cloud",
        "https://cet.lightspeedstage.cloud",
        "https://cet.lightspeeddms.cloud",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Expose all headers to the client
    max_age=3600,  # Cache preflight requests for 1 hour
)

#
# Create Mangum app wrapper (for lambda)
#
handler = Mangum(
    app=server,
    api_gateway_base_path='/',
    lifespan="off"
    )

#
# Register Routes
#
logger.info('Registering routes...')
server.include_router(routes.router)

logger.info(server.routes)

@server.get("/health")
def health() -> Response:
    """
    Health check endpoint.

    Returns:
        dict: Simple message confirming API is operational
    """
    return Response({"status": "OK"}) 

#
# Test Server Starting
#
if __name__ == "__main__":
    logger.info('Starting uvicorn server on http://0.0.0.0:8000')
    uvicorn.run(
        server,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        access_log=False,
        log_config=None  # Use our custom logging configuration instead of yaml file
    )
