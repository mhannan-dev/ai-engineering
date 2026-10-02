"""Base repository pattern interface."""


class BaseRepository[T]:
    """Generic repository interface defining CRUD operations."""

    def get_by_id(self, item_id: str) -> T | None:
        """Retrieve an entity by primary identifier."""
        raise NotImplementedError

    def list_all(self) -> list[T]:
        """Retrieve all entity records."""
        raise NotImplementedError

    def create(self, item: T) -> T:
        """Persist a new entity record."""
        raise NotImplementedError

    def delete(self, item_id: str) -> bool:
        """Remove an entity by identifier."""
        raise NotImplementedError
