import os
import sys
import json
import pytest
from datetime import datetime
from pydantic import ValidationError
from context_portal_mcp.db import models, database as db
from context_portal_mcp.handlers import mcp_handlers as H

# Ensure 'src' is on sys.path for imports when running tests from repo root
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


def as_dict(obj):
    """Helper to convert objects to dictionaries for assertion."""
    if isinstance(obj, dict):
        return obj
    try:
        return obj.model_dump(mode="json")
    except Exception:
        return json.loads(json.dumps(obj, default=str))


class TestProductInfoModels:
    """Test Pydantic models for product_info."""

    WS = "test_workspace"

    def test_product_info_model_creation(self):
        """Test creating a ProductInfo model with valid data."""
        product_info = models.ProductInfo(
            category="Documentation",
            summary="API Reference",
            content="Comprehensive API documentation",
            additionalFields={"version": "1.0", "status": "published"},
            tags=["api", "docs"]
        )
        assert product_info.category == "Documentation"
        assert product_info.summary == "API Reference"
        assert product_info.content == "Comprehensive API documentation"
        assert product_info.additionalFields["version"] == "1.0"
        assert "api" in product_info.tags
        assert isinstance(product_info.timestamp, datetime)

    def test_product_info_model_defaults(self):
        """Test ProductInfo model with default values."""
        product_info = models.ProductInfo(
            category="Test",
            summary="Test summary",
            content="Test content"
        )
        assert product_info.additionalFields == {}
        assert product_info.tags is None
        assert product_info.id is None

    def test_add_product_info_args_valid(self):
        """Test AddProductInfoArgs with valid data."""
        args = models.AddProductInfoArgs(
            workspace_id=self.WS,
            category="Test",
            summary="Summary",
            content="Content",
            additionalFields={"key": "value"},
            tags=["test", "example"]
        )
        assert args.workspace_id == self.WS
        assert args.category == "Test"
        assert args.tags == ["test", "example"]

    def test_add_product_info_args_defaults(self):
        """Test AddProductInfoArgs with default optional fields."""
        args = models.AddProductInfoArgs(
            workspace_id=self.WS,
            category="Test",
            summary="Summary",
            content="Content"
        )
        assert args.additionalFields == {}
        assert args.tags is None

    def test_add_product_info_args_missing_required(self):
        """Test AddProductInfoArgs fails without required fields."""
        with pytest.raises(ValidationError):
            models.AddProductInfoArgs(
                workspace_id=self.WS,
                category="Test"
                # Missing summary and content
            )

    def test_get_product_info_args_all_filters(self):
        """Test GetProductInfoArgs with all filtering options."""
        args = models.GetProductInfoArgs(
            workspace_id=self.WS,
            id=1,
            category="Documentation",
            limit=10,
            tags_filter_include_all=["api", "v1"],
            tags_filter_include_any=["docs", "guide"]
        )
        assert args.id == 1
        assert args.category == "Documentation"
        assert args.limit == 10

    def test_get_product_info_args_limit_validation(self):
        """Test GetProductInfoArgs limit bounds validation."""
        with pytest.raises(ValidationError):
            models.GetProductInfoArgs(
                workspace_id=self.WS,
                limit=0  # Must be >= 1
            )

    def test_get_product_info_args_limit_coercion(self):
        """Test GetProductInfoArgs limit string coercion."""
        args = models.GetProductInfoArgs(
            workspace_id=self.WS,
            limit="5"
        )
        assert args.limit == 5
        assert isinstance(args.limit, int)
    
    def test_get_product_info_tags_args_all_filters(self):
        """Test GetProductInfoArgs with all filtering options."""
        args = models.GetProductInfoTagsArgs(
            workspace_id=self.WS,
            category="Documentation",
            limit=10,
        )
        assert args.category == "Documentation"
        assert args.limit == 10

    def test_get_product_info_tags_args_limit_validation(self):
        """Test GetProductInfoArgs limit bounds validation."""
        with pytest.raises(ValidationError):
            models.GetProductInfoTagsArgs(
                workspace_id=self.WS,
                limit=0  # Must be >= 1
            )

    def test_get_product_info__tags_args_limit_coercion(self):
        """Test GetProductInfoArgs limit string coercion."""
        args = models.GetProductInfoTagsArgs(
            workspace_id=self.WS,
            limit="5"
        )
        assert args.limit == 5
        assert isinstance(args.limit, int)

    def test_update_product_info_args_valid(self):
        """Test UpdateProductInfoArgs with valid data."""
        args = models.UpdateProductInfoArgs(
            workspace_id=self.WS,
            id=1,
            category="Updated",
            additionalFields={"new_key": "new_value"}
        )
        assert args.id == 1
        assert args.category == "Updated"

    def test_update_product_info_args_no_fields_fails(self):
        """Test UpdateProductInfoArgs fails when no fields to update."""
        with pytest.raises(ValidationError):
            models.UpdateProductInfoArgs(
                workspace_id=self.WS,
                id=1
                # No fields to update
            )

    def test_update_product_info_args_id_bounds(self):
        """Test UpdateProductInfoArgs id validation."""
        with pytest.raises(ValidationError):
            models.UpdateProductInfoArgs(
                workspace_id=self.WS,
                id=0,  # Must be >= 1
                category="Test"
            )

    def test_update_product_info_args_id_coercion(self):
        """Test UpdateProductInfoArgs id string coercion."""
        args = models.UpdateProductInfoArgs(
            workspace_id=self.WS,
            id="42",
            category="Test"
        )
        assert args.id == 42
        assert isinstance(args.id, int)

    def test_delete_product_info_args_valid(self):
        """Test DeleteProductInfoArgs with valid id."""
        args = models.DeleteProductInfoArgs(
            workspace_id=self.WS,
            id=1
        )
        assert args.id == 1

    def test_delete_product_info_args_id_bounds(self):
        """Test DeleteProductInfoArgs id validation."""
        with pytest.raises(ValidationError):
            models.DeleteProductInfoArgs(
                workspace_id=self.WS,
                id=-1  # Must be >= 1
            )

    def test_delete_product_info_args_id_coercion(self):
        """Test DeleteProductInfoArgs id string coercion."""
        args = models.DeleteProductInfoArgs(
            workspace_id=self.WS,
            id="99"
        )
        assert args.id == 99


class TestProductInfoHandlers:
    """Test handler functions for product_info operations."""

    @classmethod
    def setup_class(cls):
        """Set up test workspace."""
        cls.workspace_id = os.getcwd()

    def test_handle_add_product_info(self):
        """Test adding a new product_info entry."""
        args = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="API",
            summary="REST API Documentation",
            content="Complete REST API reference with examples",
            additionalFields={"version": "2.0", "status": "stable"},
            tags=["api", "rest", "v2"]
        )
        
        result = H.handle_add_product_info(args)
        result_dict = as_dict(result)
        
        assert result_dict["status"] == "success"
        assert "id" in result_dict
        assert isinstance(result_dict["id"], int)
        assert result_dict["id"] > 0

    def test_handle_add_product_info_minimal(self):
        """Test adding product_info with minimal fields."""
        args = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Notes",
            summary="Quick note",
            content="This is a note"
        )
        
        result = H.handle_add_product_info(args)
        result_dict = as_dict(result)
        
        assert result_dict["status"] == "success"
        assert "id" in result_dict

    def test_handle_get_product_info_all(self):
        """Test retrieving all product_info entries."""
        # First add an entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test entry",
            content="Test content",
            tags=["test"]
        )
        H.handle_add_product_info(args_add)
        
        # Now retrieve
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id
        )
        
        results = H.handle_get_product_info(args_get)
        
        assert isinstance(results, list)
        assert len(results) > 0

    def test_handle_get_product_info_by_id(self):
        """Test retrieving product_info by specific id."""
        # Add an entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Specific",
            summary="Specific entry",
            content="Specific content"
        )
        
        add_result = H.handle_add_product_info(args_add)
        added_id = as_dict(add_result)["id"]
        
        # Retrieve by id
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id,
            id=added_id
        )
        
        results = H.handle_get_product_info(args_get)
        
        assert len(results) > 0
        assert results[0]["id"] == added_id

    def test_handle_get_product_info_by_category(self):
        """Test filtering product_info by category."""
        # Add entries with different categories
        args1 = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="CategoryA",
            summary="Entry 1",
            content="Content 1"
        )
        H.handle_add_product_info(args1)
        
        args2 = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="CategoryB",
            summary="Entry 2",
            content="Content 2"
        )
        H.handle_add_product_info(args2)
        
        # Retrieve by category
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id,
            category="CategoryA"
        )
        
        results = H.handle_get_product_info(args_get)
        
        assert len(results) > 0
        for item in results:
            assert item["category"] == "CategoryA"

    def test_handle_get_product_info_with_limit(self):
        """Test retrieving product_info with limit."""

        # First add 2 entries
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test entry",
            content="Test content",
            tags=["test"]
        )
        H.handle_add_product_info(args_add)

        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test2",
            summary="Test entry2",
            content="Test content2",
            tags=["test2"]
        )
        H.handle_add_product_info(args_add)

        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id,
            limit=1
        )
        
        results = H.handle_get_product_info(args_get)
        
        assert isinstance(results, list)
        assert len(results) == 1
    
    def test_handle_get_product_info_tags_all(self):
        """Test retrieving all product_info tags."""
        # First add 2 entries
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test entry",
            content="Test content",
            tags=["test"]
        )
        H.handle_add_product_info(args_add)

        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test2",
            summary="Test entry2",
            content="Test content2",
            tags=["test2"]
        )
        H.handle_add_product_info(args_add)
        
        # Now retrieve
        args_get = models.GetProductInfoTagsArgs(
            workspace_id=self.workspace_id
        )
        
        results = H.handle_get_product_info_tags(args_get)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert "test" in results
        assert "test2" in results
    
    def test_handle_get_product_info_tags_by_category(self):
        """Test retrieving all product_info tags filtered by category."""
        # First add 2 entries
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test entry",
            content="Test content",
            tags=["test"]
        )
        H.handle_add_product_info(args_add)

        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test2",
            summary="Test entry2",
            content="Test content2",
            tags=["test2"]
        )
        H.handle_add_product_info(args_add)
        
        # Now retrieve
        args_get = models.GetProductInfoTagsArgs(
            workspace_id=self.workspace_id,
            category = "Test"
        )
        
        results = H.handle_get_product_info_tags(args_get)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert "test" in results
        assert "test2" not in results
    
    def test_handle_get_product_info_tags_with_limit(self):
        """Test retrieving product_info tags with limit."""

        # First add 2 entries
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test entry",
            content="Test content",
            tags=["test"]
        )
        H.handle_add_product_info(args_add)

        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test2",
            summary="Test entry2",
            content="Test content2",
            tags=["test2"]
        )
        H.handle_add_product_info(args_add)

        args_get = models.GetProductInfoTagsArgs(
            workspace_id=self.workspace_id,
            limit=1
        )
        
        results = H.handle_get_product_info_tags(args_get)
        
        assert isinstance(results, list)
        assert len(results) == 1

    def test_handle_update_product_info_category(self):
        """Test updating product_info category."""
        # Add entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Original",
            summary="Original summary",
            content="Original content"
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        
        # Update category
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id,
            category="Updated"
        )
        
        update_result = H.handle_update_product_info(args_update)
        update_dict = as_dict(update_result)
        
        assert update_dict["status"] == "success"

    def test_handle_update_product_info_content(self):
        """Test updating product_info content."""
        # Add entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Original",
            content="Original content"
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        
        # Update content
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id,
            content="New content"
        )
        
        update_result = H.handle_update_product_info(args_update)
        update_dict = as_dict(update_result)
        
        assert update_dict["status"] == "success"

    def test_handle_update_product_info_additional_fields(self):
        """Test updating additionalFields."""
        # Add entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test",
            content="Test",
            additionalFields={"old_key": "old_value"}
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        
        # Update additionalFields
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id,
            additionalFields={"new_key": "new_value"}
        )
        
        update_result = H.handle_update_product_info(args_update)
        update_dict = as_dict(update_result)
        
        assert update_dict["status"] == "success"

    def test_handle_update_product_info_tags(self):
        """Test updating tags."""
        # Add entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="Test",
            content="Test",
            tags=["old"]
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        
        # Update tags
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id,
            tags=["new", "updated"]
        )
        
        update_result = H.handle_update_product_info(args_update)
        update_dict = as_dict(update_result)
        
        assert update_dict["status"] == "success"

    def test_handle_update_product_info_not_found(self):
        """Test updating non-existent product_info."""
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=999999,
            category="Test"
        )
        
        result = H.handle_update_product_info(args_update)
        result_dict = as_dict(result)
        
        assert result_dict["status"] == "error"

    def test_handle_delete_product_info(self):
        """Test deleting product_info."""
        # Add entry
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Test",
            summary="To delete",
            content="Will be deleted"
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        
        # Delete
        args_delete = models.DeleteProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id
        )
        
        delete_result = H.handle_delete_product_info(args_delete)
        delete_dict = as_dict(delete_result)
        
        assert delete_dict["status"] == "success"

    def test_handle_delete_product_info_not_found(self):
        """Test deleting non-existent product_info."""
        args_delete = models.DeleteProductInfoArgs(
            workspace_id=self.workspace_id,
            id=999999
        )
        
        result = H.handle_delete_product_info(args_delete)
        result_dict = as_dict(result)
        
        assert result_dict["status"] == "error"


class TestProductInfoDatabase:
    """Test database functions for product_info."""

    @classmethod
    def setup_class(cls):
        """Set up test workspace."""
        cls.workspace_id = os.getcwd()

    def test_db_add_and_retrieve_product_info(self):
        """Test database add and retrieval."""
        product_info = models.ProductInfo(
            category="Database Test",
            summary="DB test summary",
            content="DB test content",
            additionalFields={"db": "test"},
            tags=["database", "test"]
        )
        
        # Add
        result = db.add_product_info(self.workspace_id, product_info)
        
        assert result.id is not None
        assert result.category == "Database Test"
        
        # Retrieve
        items = db.get_product_info(self.workspace_id, product_id=result.id)
        
        assert len(items) > 0
        assert items[0].id == result.id
        assert items[0].category == "Database Test"

    def test_db_get_product_info_by_category(self):
        """Test database retrieval by category."""
        product_info = models.ProductInfo(
            category="UniqueCategory",
            summary="Summary",
            content="Content"
        )
        
        db.add_product_info(self.workspace_id, product_info)
        
        items = db.get_product_info(
            self.workspace_id,
            category="UniqueCategory"
        )
        
        assert len(items) > 0
        for item in items:
            assert item.category == "UniqueCategory"

    def test_db_update_product_info(self):
        """Test database update."""
        # Add
        product_info = models.ProductInfo(
            category="Before",
            summary="Before summary",
            content="Before content"
        )
        
        added = db.add_product_info(self.workspace_id, product_info)
        
        # Update
        updates = {
            "category": "After",
            "summary": "After summary"
        }
        
        success = db.update_product_info(
            self.workspace_id,
            added.id,
            updates
        )
        
        assert success is True
        
        # Verify
        items = db.get_product_info(self.workspace_id, product_id=added.id)
        assert items[0].category == "After"
        assert items[0].summary == "After summary"

    def test_db_update_additional_fields(self):
        """Test database update of additionalFields."""
        # Add with initial additionalFields
        product_info = models.ProductInfo(
            category="Test",
            summary="Test",
            content="Test",
            additionalFields={"key1": "value1"}
        )
        
        added = db.add_product_info(self.workspace_id, product_info)
        
        # Update additionalFields
        updates = {
            "additionalFields": {"key2": "value2", "key3": "value3"}
        }
        
        success = db.update_product_info(
            self.workspace_id,
            added.id,
            updates
        )
        
        assert success is True

    def test_db_delete_product_info(self):
        """Test database deletion."""
        # Add
        product_info = models.ProductInfo(
            category="To Delete",
            summary="Will be deleted",
            content="Content"
        )
        
        added = db.add_product_info(self.workspace_id, product_info)
        entry_id = added.id
        
        # Delete
        success = db.delete_product_info(self.workspace_id, entry_id)
        
        assert success is True
        
        # Verify deletion
        items = db.get_product_info(self.workspace_id, product_id=entry_id)
        assert len(items) == 0

    def test_db_delete_not_found(self):
        """Test deleting non-existent entry."""
        success = db.delete_product_info(self.workspace_id, 999999)
        
        assert success is False

    def test_db_get_product_info_tags_by_category(self):
        """Test database retrieval of tags by category."""
        product_info = models.ProductInfo(
            category="UniqueCategory",
            summary="Summary",
            content="Content",
            tags = ["unique-category"]
        )
        
        db.add_product_info(self.workspace_id, product_info)
        
        items = db.get_product_info_tags(
            self.workspace_id,
            category="UniqueCategory"
        )
        
        assert items == ["unique-category"]


class TestProductInfoIntegration:
    """Integration tests for product_info feature."""

    @classmethod
    def setup_class(cls):
        """Set up test workspace."""
        cls.workspace_id = os.getcwd()

    def test_product_info_workflow(self):
        """Test complete product_info workflow: add, get, update, delete."""
        
        # 1. Add
        args_add = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Workflow",
            summary="Workflow test",
            content="Testing complete workflow",
            additionalFields={"step": "1"},
            tags=["workflow", "test"]
        )
        
        add_result = H.handle_add_product_info(args_add)
        entry_id = as_dict(add_result)["id"]
        assert add_result is not None
        
        # 2. Get
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id
        )
        
        items = H.handle_get_product_info(args_get)
        assert len(items) > 0
        assert items[0]["id"] == entry_id
        
        # 3. Update
        args_update = models.UpdateProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id,
            additionalFields={"step": "2", "status": "completed"}
        )
        
        update_result = H.handle_update_product_info(args_update)
        assert as_dict(update_result)["status"] == "success"
        
        # 4. Delete
        args_delete = models.DeleteProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id
        )
        
        delete_result = H.handle_delete_product_info(args_delete)
        assert as_dict(delete_result)["status"] == "success"

    def test_multiple_product_info_entries(self):
        """Test managing multiple product_info entries."""
        entries_data = [
            {
                "category": "Category1",
                "summary": "Summary 1",
                "content": "Content 1",
                "tags": ["tag1"]
            },
            {
                "category": "Category2",
                "summary": "Summary 2",
                "content": "Content 2",
                "tags": ["tag2"]
            },
            {
                "category": "Category3",
                "summary": "Summary 3",
                "content": "Content 3",
                "tags": ["tag3"]
            }
        ]
        
        added_ids = []
        
        # Add multiple entries
        for entry_data in entries_data:
            args = models.AddProductInfoArgs(
                workspace_id=self.workspace_id,
                **entry_data
            )
            result = H.handle_add_product_info(args)
            added_ids.append(as_dict(result)["id"])
        
        # Retrieve all
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id
        )
        
        results = H.handle_get_product_info(args_get)
        
        # Should have at least our added entries
        assert len(results) >= len(entries_data)
        
        # Verify each category exists
        categories = [r["category"] for r in results]
        for expected_cat in ["Category1", "Category2", "Category3"]:
            assert expected_cat in categories

    def test_product_info_with_special_characters(self):
        """Test product_info with special characters in content."""
        args = models.AddProductInfoArgs(
            workspace_id=self.workspace_id,
            category="Special",
            summary="Summary with special chars: @#$%^&*()",
            content="Content with\nnewlines\nand special chars: <>\"'{}[]",
            additionalFields={"json": '{"key": "value"}', "path": "/usr/local/bin"},
            tags=["special-chars", "test"]
        )
        
        result = H.handle_add_product_info(args)
        result_dict = as_dict(result)
        
        assert result_dict["status"] == "success"
        entry_id = result_dict["id"]
        
        # Verify retrieval
        args_get = models.GetProductInfoArgs(
            workspace_id=self.workspace_id,
            id=entry_id
        )
        
        items = H.handle_get_product_info(args_get)
        assert len(items) > 0
        assert "@#$%^&*()" in items[0]["summary"]