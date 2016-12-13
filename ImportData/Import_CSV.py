import ImportData

# SETTINGS will eventually come from an external source e.g. ArcMap, JSON, CSV
settings = ImportData.Settings('Data\\tvstations.csv')
settings.OutputFileName = "TVStations.shp"
settings.SetHeaders([
    ("Primary Network Affiliation", "TEXT"),
    ("Market Rank", "TEXT"),
    ("Licensed State", "TEXT"),
    ("Latitude (degrees)", "X"),
    ("Longitude (degrees)", "Y")])

schema = ImportData.Schema(settings)
reader= ImportData.Reader(settings, schema)

arc = ImportData.ArcAccess(settings)
arc.AddHeaders(settings.Headers)
arc.InsertDataInto(reader.Read())

    