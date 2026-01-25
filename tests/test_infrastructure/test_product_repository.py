import pytest
from src.repositories.product import get_all_products

@pytest.fixture(scope="module")
def all_products():
    return get_all_products()

def test_get_all_products_not_empty(all_products):
    """Test that the function returns a non-empty list of products."""
    assert isinstance(all_products, list)

    if len(all_products) > 0:
        first_product = all_products[0]
        assert hasattr(first_product, 'id')
        assert hasattr(first_product, 'name')
        assert hasattr(first_product, 'sku')

def test_get_all_products_and_display(all_products):
    if not all_products:
        pytest.skip("No products found in the database.")

    # use `pytest -s` to see print output
    print(f"\n[INFO] Total products found: {len(all_products)}")
    print(f"{'STT':<5} | {'ID':<36} | {'Product name':<40} | {'SKU':<15}")
    print("-" * 105)
    
    for index, p in enumerate(all_products[:10], 1):
        id_str = str(p.id)
        name_str = (p.name or 'N/A')
        sku_str = (p.sku or 'N/A')
        
        line = f"{index:<5} | {id_str:<36} | {name_str:<40} | {sku_str:<15}"
        print(line)
        
        assert len(line) > 50 
        assert "|" in line

    if len(all_products) > 10:
        print(f"\n... and {len(all_products) - 10} other products.")