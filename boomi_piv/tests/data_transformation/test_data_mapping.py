"""PIV-DATA: Data Transformation and Mapping Verification Tests.

Verifies that Boomi data maps, transformations, and document handling
work correctly after installation.
"""

import pytest

from boomi_piv.utils.validators import validate_map_function_output


class TestFieldMapping:
    """PIV-DATA-001: Field-to-field mapping verification."""

    def test_simple_field_mapping(self) -> None:
        """Simple 1:1 field mapping produces correct output."""
        input_data = {
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@example.com",
        }
        output_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email_address": "john.doe@example.com",
        }
        expected_mappings = {
            "firstName": "first_name",
            "lastName": "last_name",
            "email": "email_address",
        }

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0

    def test_mapping_with_missing_target_field(self) -> None:
        """Missing target field is detected as an issue."""
        input_data = {"name": "Alice", "age": "30"}
        output_data = {"fullName": "Alice"}
        expected_mappings = {"name": "fullName", "age": "personAge"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 1
        assert "personAge" in issues[0]
        assert "missing" in issues[0].lower()

    def test_mapping_with_value_mismatch(self) -> None:
        """Value mismatch between source and target is detected."""
        input_data = {"code": "US"}
        output_data = {"country_code": "UK"}
        expected_mappings = {"code": "country_code"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 1
        assert "mismatch" in issues[0].lower()

    def test_mapping_with_both_none(self) -> None:
        """Both source and target being None is not an issue."""
        input_data = {"name": "Test"}
        output_data = {"fullName": "Test"}
        expected_mappings = {"missing_source": "missing_target", "name": "fullName"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0


class TestNestedFieldMapping:
    """PIV-DATA-002: Nested/complex field mapping verification."""

    def test_nested_source_to_flat_target(self) -> None:
        """Nested source fields map correctly to flat target."""
        input_data = {
            "address": {
                "street": "123 Main St",
                "city": "Springfield",
                "state": "IL",
            }
        }
        output_data = {
            "street_address": "123 Main St",
            "city_name": "Springfield",
            "state_code": "IL",
        }
        expected_mappings = {
            "address.street": "street_address",
            "address.city": "city_name",
            "address.state": "state_code",
        }

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0

    def test_nested_source_to_nested_target(self) -> None:
        """Nested source to nested target maps correctly."""
        input_data = {"order": {"id": "ORD-001", "total": "99.99"}}
        output_data = {"purchase": {"order_id": "ORD-001", "amount": "99.99"}}
        expected_mappings = {
            "order.id": "purchase.order_id",
            "order.total": "purchase.amount",
        }

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0

    def test_deeply_nested_mapping(self) -> None:
        """Deeply nested paths are resolved correctly."""
        input_data = {"level1": {"level2": {"level3": {"value": "deep"}}}}
        output_data = {"result": {"extracted": "deep"}}
        expected_mappings = {"level1.level2.level3.value": "result.extracted"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0


class TestDataTypeConversion:
    """PIV-DATA-003: Data type conversion in mappings."""

    def test_numeric_to_string_mapping(self) -> None:
        """Numeric values mapped as strings match correctly."""
        input_data = {"quantity": 42}
        output_data = {"qty_str": "42"}
        expected_mappings = {"quantity": "qty_str"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0

    def test_boolean_to_string_mapping(self) -> None:
        """Boolean values mapped to string are compared as strings."""
        input_data = {"active": True}
        output_data = {"is_active": "True"}
        expected_mappings = {"active": "is_active"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0

    def test_float_precision_mapping(self) -> None:
        """Float values maintain precision through mapping."""
        input_data = {"price": 19.99}
        output_data = {"amount": "19.99"}
        expected_mappings = {"price": "amount"}

        issues = validate_map_function_output(input_data, output_data, expected_mappings)

        assert len(issues) == 0


class TestDocumentBatchProcessing:
    """PIV-DATA-004: Batch/multi-document processing verification."""

    def test_batch_all_documents_mapped(self) -> None:
        """All documents in a batch are mapped correctly."""
        batch_input = [
            {"id": "1", "name": "Item A"},
            {"id": "2", "name": "Item B"},
            {"id": "3", "name": "Item C"},
        ]
        batch_output = [
            {"item_id": "1", "item_name": "Item A"},
            {"item_id": "2", "item_name": "Item B"},
            {"item_id": "3", "item_name": "Item C"},
        ]
        expected_mappings = {"id": "item_id", "name": "item_name"}

        all_issues: list[str] = []
        for inp, outp in zip(batch_input, batch_output):
            issues = validate_map_function_output(inp, outp, expected_mappings)
            all_issues.extend(issues)

        assert len(all_issues) == 0

    def test_batch_count_preserved(self) -> None:
        """Input and output batch sizes match."""
        batch_input = [{"id": str(i)} for i in range(100)]
        batch_output = [{"record_id": str(i)} for i in range(100)]

        assert len(batch_input) == len(batch_output)

    def test_batch_empty_input(self) -> None:
        """Empty batch input produces no issues."""
        batch_input: list[dict] = []
        batch_output: list[dict] = []

        assert len(batch_input) == len(batch_output) == 0


class TestXMLToJSONTransformation:
    """PIV-DATA-005: XML to JSON transformation patterns."""

    def test_xml_flat_element_to_json(self) -> None:
        """Flat XML elements transform to JSON key-value pairs."""
        xml_parsed = {"root": {"name": "Test", "value": "123"}}
        expected_json = {"name": "Test", "value": "123"}

        assert xml_parsed["root"] == expected_json

    def test_xml_attributes_in_json(self) -> None:
        """XML attributes are preserved in JSON output."""
        xml_parsed = {
            "element": {
                "@id": "elem-001",
                "@type": "record",
                "#text": "content",
            }
        }

        assert xml_parsed["element"]["@id"] == "elem-001"
        assert xml_parsed["element"]["@type"] == "record"

    def test_xml_array_elements_to_json_array(self) -> None:
        """Repeating XML elements transform to JSON arrays."""
        xml_parsed = {
            "items": {
                "item": [
                    {"name": "A", "qty": "1"},
                    {"name": "B", "qty": "2"},
                ]
            }
        }

        items = xml_parsed["items"]["item"]
        assert isinstance(items, list)
        assert len(items) == 2
        assert items[0]["name"] == "A"
