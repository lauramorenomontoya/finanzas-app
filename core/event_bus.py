from typing import Callable, Dict, List, Any

class EventBus:
    """
    Gestor de Estado Centralizado (Patrón Pub/Sub).
    Permite desacoplar componentes para que no tengan que pasarse callbacks
    como `on_data_changed` a través de múltiples niveles (Prop Drilling).
    """
    _subscribers: Dict[str, List[Callable[..., None]]] = {}

    @classmethod
    def subscribe(cls, event_type: str, callback: Callable[..., None]):
        """Suscribe una función a un tipo de evento específico."""
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        if callback not in cls._subscribers[event_type]:
            cls._subscribers[event_type].append(callback)

    @classmethod
    def unsubscribe(cls, event_type: str, callback: Callable[..., None]):
        """Elimina la suscripción de una función a un evento."""
        if event_type in cls._subscribers:
            if callback in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(callback)

    @classmethod
    def publish(cls, event_type: str, *args, **kwargs):
        """Emite un evento a todos los suscriptores con protección contra excepciones."""
        if event_type in cls._subscribers:
            for callback in list(cls._subscribers[event_type]):
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error en suscriptor de EventBus para '{event_type}': {e}", exc_info=True)

    @classmethod
    def clear(cls):
        """Limpia todos los suscriptores (útil para tests)."""
        cls._subscribers.clear()
