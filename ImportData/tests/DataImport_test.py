import unittest
import sys

sys.path.append('C:\\PSUGIS\\GEOG485\\Final\\')

import ImportData

settings = ImportData.Settings('Data\\powerplants.xlsx')
settings.OutputFileName = "output.shp"
settings.Headers = [
    ImportData.IHeader("Id", "TEXT"),
    ImportData.IHeader("Name", "TEXT"),
    ImportData.IHeader("Latitude", "X"),
    ImportData.IHeader("Longitude", "Y")]

class TestDataImport(unittest.TestCase):

    def test_reader_initialize(self):        
        schema = ImportData.Schema(settings)
        reader = ImportData.Reader(settings, settings)
        self.assertEqual(reader.FileType, '.xlsx')

    def test_schema_creation(self):
        schema = ImportData.Schema(settings)

        self.assertEqual(4, len(schema.Headers))
        column = schema.Get("Latitude")
        self.assertEqual("X", column.Type)
        self.assertEqual("Latitude", column.Name)

    def test_row_creation(self):
        schema = ImportData.Schema(settings)

        row1 = ImportData.Row(schema)
        row1.Add("Id", 19020)
        row1.Add("Longitude", 45.123456)
        
        row2 = ImportData.Row(schema)
        row2.Add("Id", 19022)
        row2.Add("Latitude", 90.123445)

        self.assertEqual(19020, row1.ValueAt["Id"])
        self.assertEqual(19022, row2.ValueAt["Id"])

        self.assertEqual(45.123456, row1.ValueAt["Longitude"])
        self.assertEqual(90.123445, row2.ValueAt["Latitude"])
        

if __name__ == '__main__':
    unittest.main()