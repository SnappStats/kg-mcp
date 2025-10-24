from pydantic import BaseModel, Field
from typing import Optional, Any


class Relationship(BaseModel):
    """A relationship between two entities."""
    source_entity_id: str = Field(
        ...,
        description="The name of the source entity."
    )
    target_entity_id: str = Field(
        ...,
        description="The name of the target entity."
    )
    relationship: str = Field(
        ...,
        description="The description of the relationship."
    )


class Entity(BaseModel):
    """Represents an entity in the knowledge graph."""
    entity_id: str = Field(
        ...,
        description="The ID of the entity to update."
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="The timestamp when the entity was last updated."
    )
    updated_by: Optional[str] = Field(
        default=None,
        description="The user who last updated the entity."
    )
    entity_names: list[str] = Field(
        ...,
        description="A list of names for the entity, with the first being the primary name."
    )
    properties: dict[str, Any] = Field(
        default={},
        description="A dictionary of properties for the entity."
    )

class KnowledgeGraph(BaseModel):
    """Represents a knowledge graph with entities and relationships."""
    entities: list[Entity] = Field(
        default_factory=list,
        description="A list of entities in the knowledge graph."
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="A list of relationships between entities in the knowledge graph."
    )
