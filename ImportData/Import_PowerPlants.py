import ImportData

# SETTINGS will eventually come from an external source e.g. ArcMap, JSON, CSV
settings = ImportData.Settings('Data\\powerplants.xlsx')
settings.OutputFileName = "PowerPlants.shp"
settings.SetHeaders([
    ("Name", "TEXT"),
    ("Latitude", "X"),
    ("Longitude", "Y")])

schema = ImportData.Schema(settings)
reader= ImportData.Reader(settings, schema)
arc = ImportData.ArcAccess(settings)

arc.AddHeaders(settings.Headers)
arc.InsertDataInto(reader.Read())

    