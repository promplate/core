"""Tests for the ChainContext behavior."""

from collections import ChainMap

from pytest import raises

from promplate import ChainContext


def test_inheritance():
    assert issubclass(ChainContext, ChainMap)
    assert issubclass(ChainContext, dict)

    ctx = ChainContext()
    assert isinstance(ctx, ChainMap)
    assert isinstance(ctx, dict)


def test_initialization():
    # Test initialization with no arguments
    ctx = ChainContext()
    assert isinstance(ctx, ChainContext)

    # Test initialization with a single mapping
    mapping = {"key": "value"}
    ctx = ChainContext(mapping)
    assert ctx["key"] == "value"

    # Test initialization with multiple mappings
    ctx = ChainContext({"a": 1}, {"b": 2}, {"c": 3})
    assert ctx["a"] == 1
    assert ctx["b"] == 2
    assert ctx["c"] == 3


def test_maps_property():
    # Test initializing without arguments
    ctx = ChainContext()
    assert isinstance(ctx, ChainContext)
    assert ctx.maps == [{}]

    # Test initializing with a single mapping
    initial_map = {"key": "value"}
    ctx = ChainContext(initial_map)
    assert ctx.maps == [initial_map]

    # Test initializing with multiple mappings
    ctx = ChainContext(initial_map, {"another_key": "another_value"})
    assert ctx.maps == [initial_map, {"another_key": "another_value"}]


def test_result_property_edge_cases():
    ctx = ChainContext()

    # Test getting result property when not set
    with raises(KeyError):
        _ = ctx.result

    # Test deleting result property when not set
    with raises(KeyError):
        del ctx.result


def test_mapping_update():
    base_map = {"key": "original_value"}
    ctx = ChainContext(base_map)

    # Update key in ChainContext
    ctx["key"] = "new_value"
    assert ctx["key"] == "new_value"
    assert base_map["key"] == "new_value", "Confirm base map is updated"


def test_chain_update():
    base_map = {"key": "value"}
    additional_map = {"another_key": "another_value"}
    ctx = ChainContext(base_map, additional_map)

    # Update existing key
    ctx["key"] = "new_value"
    assert ctx["key"] == "new_value"
    assert "key" in base_map, "should add to the first map"


def test_map_shadowing():
    first_map = {"key": "first_value"}
    second_map = {"key": "second_value", "unique": "unique_second"}
    ctx = ChainContext(first_map, second_map)

    # Key should return value from first map
    assert ctx["key"] == "first_value"

    # Key unique to second map should be accessible
    assert ctx["unique"] == "unique_second"


def test_iteration_and_length():
    ctx = ChainContext({"a": 1}, {"b": 2, "c": 3})

    # Test length
    assert len(ctx) == 3

    # Test iteration
    keys = set(ctx.keys())
    assert keys == {"a", "b", "c"}


def test_item_deletion():
    base_map = {"key": "value"}
    ctx = ChainContext(base_map)

    # Delete an item
    del ctx["key"]
    assert "key" not in ctx
    assert "key" not in base_map, "Confirm deletion from base map"

    # Attempt to delete a non-existing item
    with raises(KeyError):
        del ctx["non_existing_key"]


def test_result_property():
    ctx = ChainContext()
    ctx.result = "test_result"
    assert ctx.result == "test_result"
    assert "__result__" in ctx
    assert ctx["__result__"] == "test_result"
    del ctx.result
    with raises(KeyError):
        _ = ctx.result


def test_as_chain_map():
    # Test the ChainMap functionality of ChainContext
    ctx = ChainContext({"key1": "value1"}, {"key1": "value2", "key2": "value2"})
    assert ctx["key1"] == "value1"
    assert ctx["key2"] == "value2"

    # Test updates
    ctx["key1"] = "new_value"
    assert ctx["key1"] == "new_value"
    assert ctx.maps[0]["key1"] == "new_value"


def test_result_property_2():
    # Test setting and getting the result property
    ctx = ChainContext()
    ctx.result = "test_result"
    assert ctx.result == "test_result"
    assert ctx["__result__"] == "test_result"

    # Test deleting the result property
    del ctx.result
    with raises(KeyError):
        _ = ctx.result


def test_ensure_method():
    # Test ensure method with ChainContext instance
    ctx = ChainContext()
    new_ctx = ChainContext.ensure(ctx)
    assert new_ctx is ctx

    # Test ensure method with a non-ChainContext instance
    dict_ctx = {"key": "value"}
    new_ctx = ChainContext.ensure(dict_ctx)
    assert isinstance(new_ctx, ChainContext)
    assert new_ctx.maps[0] is dict_ctx

    assert new_ctx["key"] == "value"
    assert len(new_ctx.maps) == 1
    assert len(new_ctx) == 1


def test_subclass():
    class MyChainContext(ChainContext):
        pass

    ctx = MyChainContext()

    assert isinstance(ChainContext(ctx), MyChainContext)

    assert isinstance(ChainContext.ensure(ctx), MyChainContext)
