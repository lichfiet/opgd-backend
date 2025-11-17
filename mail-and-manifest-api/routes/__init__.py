from ._router import router

# Import route modules to register them
import routes.contact
import routes.content
import routes.manifests

__all__ = ["router"]