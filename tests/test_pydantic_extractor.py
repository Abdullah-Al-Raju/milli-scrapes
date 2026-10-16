import unittest
from typing import Optional
from pydantic import BaseModel
from milli_scrapes.extractor.pydantic_extractor import PydanticExtractor


class ProductItem(BaseModel):
    name: str
    price: str
    in_stock: bool = True
    sku: Optional[str] = None


class TestPydanticExtractor(unittest.TestCase):

    def test_pydantic_extraction_with_css(self):
        html = """
        <html>
          <body>
            <h1 class="prod-name">Turbo Graphics Card</h1>
            <span class="prod-price">$799.00</span>
            <div id="sku">GPU-9090</div>
          </body>
        </html>
        """
        item = PydanticExtractor.extract_from_html(
            html,
            ProductItem,
            css_selectors={"name": ".prod-name", "price": ".prod-price", "sku": "#sku"}
        )
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Turbo Graphics Card")
        self.assertEqual(item.price, "$799.00")
        self.assertEqual(item.sku, "GPU-9090")
        self.assertTrue(item.in_stock)

    def test_json_schema_generation(self):
        schema = PydanticExtractor.get_json_schema(ProductItem)
        self.assertIn("properties", schema)
        self.assertIn("name", schema["properties"])
        self.assertIn("price", schema["properties"])


if __name__ == "__main__":
    unittest.main()
