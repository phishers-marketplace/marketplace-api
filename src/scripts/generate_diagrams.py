#!/usr/bin/env python3
"""
Script to generate ER diagrams and schema visualizations for the MongoDB models.
Generates both a text-based representation and graphical diagrams.
"""

import json
import os
import sys
from typing import Dict, List, Set, Type, Union, get_type_hints

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import networkx as nx
from beanie import Document
from matplotlib.lines import Line2D

# Import all document models
from business.friends.models import Friendship
from business.groups.models import Group, GroupMembership
from business.marketplace.items.models import Item
from business.marketplace.transactions.models import Transaction
from business.user.models import User


def get_all_document_classes() -> List[Type[Document]]:
    """Get all Beanie Document classes in the codebase."""
    return [User, Friendship, Group, GroupMembership, Item, Transaction]


def extract_field_info(model_class: Type[Document]) -> Dict:
    """Extract field info from a Beanie Document class."""
    type_hints = get_type_hints(model_class)
    fields = {}

    for field_name, field_type in type_hints.items():
        if field_name.startswith("_"):
            continue

        # Convert complex types to string representation
        if hasattr(field_type, "__origin__"):
            if field_type.__origin__ is list or field_type.__origin__ is List:
                inner_type = str(field_type.__args__[0]).replace("<class '", "").replace("'>", "")
                field_type_str = f"List[{inner_type}]"
            elif field_type.__origin__ is dict or field_type.__origin__ is Dict:
                key_type = str(field_type.__args__[0]).replace("<class '", "").replace("'>", "")
                val_type = str(field_type.__args__[1]).replace("<class '", "").replace("'>", "")
                field_type_str = f"Dict[{key_type}, {val_type}]"
            elif (
                field_type.__origin__ is Union
                or field_type.__origin__ is type(None)
                or str(field_type.__origin__) == "typing.Union"
            ):
                if type(None) in field_type.__args__:
                    # This is an Optional type
                    other_types = [t for t in field_type.__args__ if t is not type(None)]
                    if len(other_types) == 1:
                        inner_type = str(other_types[0]).replace("<class '", "").replace("'>", "")
                        field_type_str = f"Optional[{inner_type}]"
                    else:
                        types_str = ", ".join(str(t).replace("<class '", "").replace("'>", "") for t in other_types)
                        field_type_str = f"Optional[Union[{types_str}]]"
                else:
                    types_str = ", ".join(str(t).replace("<class '", "").replace("'>", "") for t in field_type.__args__)
                    field_type_str = f"Union[{types_str}]"
            else:
                field_type_str = str(field_type)
        else:
            field_type_str = str(field_type).replace("<class '", "").replace("'>", "")

        # Check if it's a foreign key reference
        is_reference = False
        reference_to = None
        if field_name.endswith("_id"):
            potential_model_name = field_name[:-3].capitalize()
            is_reference = True
            reference_to = potential_model_name

        fields[field_name] = {"type": field_type_str, "is_reference": is_reference, "reference_to": reference_to}

    return fields


def generate_text_schema(document_classes: List[Type[Document]]) -> str:
    """Generate a text-based schema representation."""
    schema_text = ""

    for model_class in document_classes:
        model_name = model_class.__name__
        collection_name = (
            model_class.Settings.name
            if hasattr(model_class, "Settings") and hasattr(model_class.Settings, "name")
            else model_name.lower()
        )

        schema_text += f"Collection: {collection_name} (Model: {model_name})\n"
        schema_text += "-" * 50 + "\n"

        fields = extract_field_info(model_class)
        for field_name, field_info in fields.items():
            reference_str = f" -> References {field_info['reference_to']}" if field_info["is_reference"] else ""
            schema_text += f"  {field_name}: {field_info['type']}{reference_str}\n"

        if hasattr(model_class, "Settings") and hasattr(model_class.Settings, "indexes"):
            schema_text += "\n  Indexes:\n"
            for idx in model_class.Settings.indexes:
                schema_text += f"    - {idx}\n"

        schema_text += "\n\n"

    return schema_text


def generate_er_diagram(document_classes: List[Type[Document]], output_file: str = "er_diagram.png"):
    """Generate an Entity-Relationship diagram as a PNG image."""
    G = nx.DiGraph()

    # Add nodes for each model
    for model_class in document_classes:
        model_name = model_class.__name__
        G.add_node(model_name)

    # Add edges for relationships
    for model_class in document_classes:
        model_name = model_class.__name__
        fields = extract_field_info(model_class)

        for field_name, field_info in fields.items():
            if field_info["is_reference"]:
                target_model = field_info["reference_to"]

                # Check if the target model exists in our model classes
                if any(cls.__name__ == target_model for cls in document_classes):
                    G.add_edge(model_name, target_model, field=field_name)
                # Special case handling for references that don't match the model name exactly
                elif field_name == "buyer_id" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "seller_id" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "requester_id" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "recipient_id" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "created_by" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "invited_by" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "user_id" and "User" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "User", field=field_name)
                elif field_name == "item_id" and "Item" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "Item", field=field_name)
                elif field_name == "group_id" and "Group" in [cls.__name__ for cls in document_classes]:
                    G.add_edge(model_name, "Group", field=field_name)

    # Draw the graph
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, seed=42, k=0.8)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color="lightblue", alpha=0.8)
    nx.draw_networkx_labels(G, pos, font_weight="bold", font_size=12)

    # Draw edges with labels
    edge_labels = {(u, v): d["field"] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=20, width=1.5, alpha=0.7)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

    # Add legend
    legend_elements = [
        Line2D([0], [0], color="black", lw=1.5, label="References"),
    ]
    plt.legend(handles=legend_elements, loc="upper right")

    plt.title("MongoDB Document Relationships", size=16)
    plt.axis("off")
    plt.tight_layout()

    # Save the figure
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"ER diagram saved to {output_file}")


def generate_detailed_schema_json(document_classes: List[Type[Document]], output_file: str = "schema.json"):
    """Generate a detailed JSON schema file for all models."""
    schema = {}

    for model_class in document_classes:
        model_name = model_class.__name__
        collection_name = (
            model_class.Settings.name
            if hasattr(model_class, "Settings") and hasattr(model_class.Settings, "name")
            else model_name.lower()
        )

        fields = extract_field_info(model_class)
        field_schema = {}
        for field_name, field_info in fields.items():
            field_schema[field_name] = {
                "type": field_info["type"],
                "is_reference": field_info["is_reference"],
                "reference_to": field_info["reference_to"],
            }

        indexes = []
        if hasattr(model_class, "Settings") and hasattr(model_class.Settings, "indexes"):
            indexes = model_class.Settings.indexes

        schema[model_name] = {"collection_name": collection_name, "fields": field_schema, "indexes": indexes}

    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"Detailed schema saved to {output_file}")


def main():
    """Main function to generate all diagrams."""
    # Create output directory if it doesn't exist
    output_dir = "diagrams"
    os.makedirs(output_dir, exist_ok=True)

    # Get all document classes
    document_classes = get_all_document_classes()

    # Generate text schema
    text_schema = generate_text_schema(document_classes)
    with open(os.path.join(output_dir, "schema.txt"), "w") as f:
        f.write(text_schema)
    print(f"Text schema saved to {os.path.join(output_dir, 'schema.txt')}")

    # Generate ER diagram
    generate_er_diagram(document_classes, os.path.join(output_dir, "er_diagram.png"))

    # Generate detailed JSON schema
    generate_detailed_schema_json(document_classes, os.path.join(output_dir, "schema.json"))

    print("All diagrams generated successfully!")


if __name__ == "__main__":
    main()
