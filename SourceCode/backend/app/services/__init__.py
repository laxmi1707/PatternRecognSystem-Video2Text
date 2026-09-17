def get_ml_service():
    from app.services.ml_service import ml_service
    return ml_service

__all__ = ["get_ml_service"]
