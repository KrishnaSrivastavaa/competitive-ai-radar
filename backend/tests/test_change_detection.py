from app.services.change_detection import detect_changes


def test_initial_snapshot():
    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        }
    ]

    result = detect_changes(
        previous_data=None,
        current_data=current,
        previous_hash=None,
        current_hash="hash_1",
    )

    assert result.change_type == "initial"
    assert result.significance == "low"
    assert len(result.diff_data["added"]) == 1
    assert result.diff_data["removed"] == []
    assert result.diff_data["modified"] == []


def test_unchanged_data():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="same_hash",
        current_hash="same_hash",
    )

    assert result.change_type == "unchanged"
    assert result.significance == "none"
    assert result.diff_data["added"] == []
    assert result.diff_data["removed"] == []
    assert result.diff_data["modified"] == []


def test_price_change_is_detected():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": {
                "value": 29.99,
                "currency": "USD",
            },
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": {
                "value": 39.99,
                "currency": "USD",
            },
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"
    assert len(result.diff_data["modified"]) == 1

    modification = result.diff_data["modified"][0]

    assert modification["record_key"] == (
        "product_page_url:https://example.com/product/1"
    )
    assert modification["changed_fields"] == ["price.value"]


def test_product_added():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
        },
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "added"
    assert result.significance == "medium"
    assert len(result.diff_data["added"]) == 1
    assert result.diff_data["added"][0]["title"] == "Product B"
    assert result.diff_data["removed"] == []
    assert result.diff_data["modified"] == []


def test_product_removed():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
        },
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "removed"
    assert result.significance == "high"
    assert len(result.diff_data["removed"]) == 1
    assert result.diff_data["removed"][0]["title"] == "Product B"
    assert result.diff_data["added"] == []
    assert result.diff_data["modified"] == []


def test_multiple_fields_are_detected():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
            "availability": "In Stock",
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A Updated",
            "price": 39.99,
            "availability": "Out of Stock",
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"
    assert len(result.diff_data["modified"]) == 1

    changed_fields = result.diff_data["modified"][0]["changed_fields"]

    assert "title" in changed_fields
    assert "price" in changed_fields
    assert "availability" in changed_fields


def test_record_order_does_not_create_false_changes():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
        },
        {
            "product_page_url": "https://example.com/product/3",
            "title": "Product C",
        },
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/3",
            "title": "Product C",
        },
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
        },
    ]

    # Hashes are intentionally different here to ensure the actual
    # record comparison handles ordering independently.
    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "unchanged"
    assert result.significance == "none"
    assert result.diff_data["added"] == []
    assert result.diff_data["removed"] == []
    assert result.diff_data["modified"] == []


def test_nested_field_change_is_detected():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "pricing": {
                "monthly": {
                    "amount": 29.99,
                    "currency": "USD",
                }
            },
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "pricing": {
                "monthly": {
                    "amount": 39.99,
                    "currency": "USD",
                }
            },
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"

    changed_fields = result.diff_data["modified"][0]["changed_fields"]

    assert "pricing.monthly.amount" in changed_fields


def test_record_with_url_identity_is_matched():
    previous = [
        {
            "url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        }
    ]

    current = [
        {
            "url": "https://example.com/product/1",
            "title": "Product A",
            "price": 39.99,
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"
    assert len(result.diff_data["modified"]) == 1
    assert (
        result.diff_data["modified"][0]["record_key"]
        == "url:https://example.com/product/1"
    )


def test_added_and_modified_can_occur_together():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        }
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 39.99,
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
            "price": 49.99,
        },
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"
    assert len(result.diff_data["added"]) == 1
    assert len(result.diff_data["modified"]) == 1

    assert result.diff_data["added"][0]["title"] == "Product B"
    assert result.diff_data["modified"][0]["changed_fields"] == ["price"]


def test_removed_and_modified_can_occur_together():
    previous = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 29.99,
        },
        {
            "product_page_url": "https://example.com/product/2",
            "title": "Product B",
            "price": 49.99,
        },
    ]

    current = [
        {
            "product_page_url": "https://example.com/product/1",
            "title": "Product A",
            "price": 39.99,
        }
    ]

    result = detect_changes(
        previous_data=previous,
        current_data=current,
        previous_hash="old_hash",
        current_hash="new_hash",
    )

    assert result.change_type == "modified"
    assert len(result.diff_data["removed"]) == 1
    assert len(result.diff_data["modified"]) == 1

    assert result.diff_data["removed"][0]["title"] == "Product B"
    assert result.diff_data["modified"][0]["changed_fields"] == ["price"]