import ImportData

# SETTINGS will eventually come from an external source e.g. ArcMap, JSON, CSV
settings = ImportData.Settings('Data\\US_WKT.xlsx')
settings.OutputFileName = "USOutline.shp"
settings.SetHeaders([
    ("Country", "TEXT"),
    ("Shape", "WKT")])

arc = ImportData.ArcAccess(settings)
arc.AddHeaders(settings.Headers)

schema = ImportData.Schema(settings)
reader= ImportData.Reader(settings, schema)
arc.InsertDataInto(reader.Read())

    