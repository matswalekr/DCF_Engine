import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from excel_code import open_excel, Excel_modify, Excel_read, Excel_write
import unittest


class Test_Excel_Code(unittest.TestCase):
    """Class to test the behaviour of the excel code of this file"""


    def setUp(self) -> None:
        self.test_file = r"tests/Test_workbook.xlsx"

    def test_open_excel(self) -> None:
        with open_excel(self.test_file, "r") as doc:
            self.assertIsInstance(doc, Excel_read)
        with open_excel(self.test_file, "m") as doc:
            self.assertIsInstance(doc, Excel_modify)
        with open_excel(self.test_file, "w") as doc:
            self.assertIsInstance(doc, Excel_write)

    def test_cell_math_one_cell(self) -> None:
        with open_excel(self.test_file, "w") as doc:
            doc["A2"] = 3
            doc["A2"] += 3
            self.assertEqual(doc["A2"].value, 6)

            doc["A2"] = 3
            doc["A2"] *= 3
            self.assertEqual(doc["A2"].value, 9)

            doc["A2"] = 3
            doc["A2"] -= 3
            self.assertEqual(doc["A2"].value, 0)

            doc["A2"] = 3
            doc["A2"] /= 3
            self.assertEqual(doc["A2"].value,1)


    def test_name_cell(self)-> None:
        with open_excel(self.test_file, "w") as doc:
            doc["A2"] = 10
            doc.name(range_ = "A2", name = "test")
            self.assertEqual(doc["A2"].value, 10)

    def test_new_sheets(self)-> None:
        with open_excel(self.test_file, "w") as doc:

            new_name = "New Sheet"
            doc.new_sheet(new_name)
            doc[new_name]["A2"] = 2
            self.assertIn(new_name, doc.sheets)

            newer_name = "Newer Sheet"
            doc.rename_sheet(new_name, newer_name)
            self.assertIn(newer_name, doc.sheets)

            #self.save()
            #self.assertEqual(doc[newer_name]["A2"].value, 2)

            doc.remove_sheet(newer_name)
            self.assertNotIn(newer_name, doc.sheets)

    def test_setting_range(self)-> None:
        with open_excel(self.test_file, "w") as doc:
            doc["A4:A8"] = 5

            self.assertEqual(doc["A4"].value, 5)
            self.assertEqual(doc["A8"].value, 5)
            self.assertEqual(doc["A5"].value, 5)


    def test_setting_formula(self)-> None:
        with open_excel(self.test_file, "w") as doc:
            doc["A3"] = 3
            doc["A4"] = 4
            doc["A5"] = "=SUM(A3:A4)"  # Set the formula

            self.assertEqual(doc.evaluate_formula("A5"), 7)  # Ensure the formula is written

            doc["A4"] = 5
            self.assertEqual(doc.evaluate_formula("A5"), 8) # Test that the change in input value also leads to a change in output
    
# run using pytest tests/ in root directory