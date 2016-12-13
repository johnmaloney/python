from collections import namedtuple
IHeader = namedtuple("IHeader", "Name,Type")

""" Holds the data and the metadata pertaining to the import source """
class Reader:
    def __init__(self, settings, schema):
        self._importedFileName = settings.ImportedFileLocation
        self._schema = schema
    
    @property
    def FileType(self):
        import os.path
        extension = os.path.splitext(self._importedFileName)[1]
        return extension 

    def Read(self):
        fileType = self.FileType
        if(fileType == '.xlsx'):
            return self.ReadExcel()
        elif(fileType == '.csv'):
            return self.ReadCsv()
        else:
            raise EnvironmentError('The file type of ' + fileType + ' is not supported.')

    def ReadExcel(self):
        import xlrd
        book = xlrd.open_workbook(self._importedFileName)
        sheet = book.sheet_by_index(0)

        from xlrd.sheet import ctype_text
        dataRows = []
        
        for rowIndex in range(0, sheet.nrows):
            if(rowIndex == 0):
                colCount = sheet.ncols                
                for columnCell in range(0, colCount):
                    # get the cell of the header Row
                    headerCell = sheet.cell(rowIndex, columnCell)
                    self._schema.Add(headerCell.value, columnCell)
            else:
                # since we have the columns in the self._schema use those
                row = Row(self._schema)
                for cellName in self._schema.ImportedColumns:
                    rowCell = sheet.cell(rowIndex,self._schema.ImportedColumns[cellName])                    
                    row.Add(cellName, rowCell.value)
                dataRows.append(row)
        # return the data        
        return dataRows

    def ReadCsv(self):
        csvText = open(self._importedFileName, "r")
        #Assuming the first lime is the headers
        header = csvText.readline()
        fieldList = header.split(",")
        headerCount = len(fieldList)
        dataRows = []

        #generate the schema
        for headerIndex in range(0, headerCount):
            self._schema.Add(fieldList[headerIndex], headerIndex)

        for line in csvText.readlines():
            segmentedLine = line.split(",")
            
            row = Row(self._schema)

            for cellName in self._schema.ImportedColumns:
                cellIndex = self._schema.ImportedColumns[cellName]
                value = segmentedLine[cellIndex]
                row.Add(cellName.strip(), value.strip())
            dataRows.append(row)
        return dataRows


''' Stores the Column information for an import data source.'''
class Schema:    
    def __init__(self, settings):
        self._importedColumns = {}
        self._outputHeaders = settings.Headers

    @property
    def Headers(self):
        return self._outputHeaders

    @property
    def ImportedColumns(self):
        return self._importedColumns

    def Add(self, columnName, ordinal):
        
        # storing the ordinal of the matched column 
        self._importedColumns[columnName] = ordinal

    def Get(self, columnName):
        return [h for h in self._outputHeaders if h.Name == columnName][0]

    def GetByIndex(self, columnIndex):
        for kvp in self._importedColumns:
            if kvp[1] == columnIndex:
                return self.Get(kvp[0])

''' Represents a single row of data from a source such as Excel, CSV, or JSON'''
class Row:
    def __init__(self, schema):
        self._schema = schema
        self._data = {}
        for header in schema.Headers:
            self._data[header.Name] = "null"
   
    @property
    def ValueAt(self):
        return self._data
    
    def Add(self, columnName, data):
            #This will block those columns that were not defined by the user in the Headers
        if any(name == columnName for name in self._data):
            self._data[columnName] = data     

    def PointValues(self):
        # Only return the non shape data
        x = [h for h in self._schema.Headers if h.Type == "X"][0]
        y = [h for h in self._schema.Headers if h.Type == "Y"][0]
        return (self._data[x.Name], self._data[y.Name])

    def WKTValue(self):
        # Only return the non shape data
        wkt = [h for h in self._schema.Headers if h.Type == "WKT"][0]
        return self._data[wkt.Name]
    
    def NonShapeValues(self, columnNamesInOrder):
        # Only return the non shape data
        data = []
        for columnName in columnNamesInOrder:
            headers = [h for h in self._schema.Headers if h.Name == columnName]
            if (len(headers) > 0):
                header = headers[0]
                if (header.Type != "X" and header.Type != "Y" and header.Type != "WKT"):
                    data.append(self._data[columnName])        
        return data

    def __str__(self):
        """Override the toString method for this object """

        text = "Row | "
        # Concatenate the field information for this object
        for cell in self._data:
            text += str(cell) + " = " + str(self._data[cell]) + " | "

        return text

''' Represents the settings for processing an import data set '''
class Settings:

    def __init__(self, fileLocation):
        import os
        # join the filename with the current directory
        self._sourceDirectory = os.path.dirname(__file__)
        self._importedFile = os.path.join(self._sourceDirectory, fileLocation)
        self._userDefinedHeaders = []

    @property
    def WorkingDirectory(self): return self._sourceDirectory

    @property
    def ImportedFileLocation(self): return self._importedFile          

    @property
    def Headers(self): return self._userDefinedHeaders 

    @property
    def OutputFileName(self): return self._outputFileName
    @OutputFileName.setter
    def OutputFileName(self, value): self._outputFileName

    @property
    # Set the spatial reference to WGS 1984 geographic coordinate system
    def Projection(self) : return 3785 #4326 #

    def SetHeaders(self, headerValues):
        for header in headerValues:
            #if header[1] == "X" or header[1] == "Y" or header[1] == "WKT"
            self._userDefinedHeaders.append(IHeader(header[0], header[1]))

''' ArcPy wrapper '''
class ArcAccess:
    def __init__(self, settings):
        self._settings = settings

        # Need to discern if the incoming data is SHAPE@ or SHAPE@XY
        xyCount = [h for h in settings.Headers if h.Type == "X" or h.Type == "Y"]      
        wktCount = [h for h in settings.Headers if h.Type == "WKT"]

        if (len(xyCount) > 0):
            self._shapeType = "SHAPE@XY"
            self._featureType = "POINT"
        elif (len(wktCount) > 0):
            self._shapeType = "SHAPE@"
            self._featureType = ""
        else:
            self._shapeType = "UNKNOWN"

        self._headerNames = []

        #'''
        import arcpy
        arcpy.env.workspace = self._settings.WorkingDirectory
        arcpy.env.overwriteOutput = True
        #'''

    def AddHeaders(self, headers):
        import arcpy
        
        try: 
            # Set the spatial reference to WGS 1984 geographic coordinate system
            #'''
            spatialRef = arcpy.SpatialReference(self._settings.Projection) 
            arcpy.CreateFeatureclass_management(self._settings.WorkingDirectory, 
                self._settings.OutputFileName, self._featureType, "", "", "", spatialRef)
            #'''      

            for header in headers: 
                # No shape data should be added yet
                if header.Type != "X" and header.Type != "Y" and header.Type != "WKT":
                    # Add the name column into the attributes
                    #header.Name
                    #header.Type
                    #'''
                    arcpy.AddField_management(
                        self._settings.OutputFileName, 
                        header.Name, header.Type)
                    #'''
                    self._headerNames.append(header.Name)

        except Exception as ex:
            ex.message
            # Report that an error occurred
            arcpy.AddError("The batch projection of the file failed." + ex.message)
        
            # REPORT all messages   
            arcpy.AddMessage(arcpy.GetMessages())
                
    def InsertDataInto(self, rows):    
  
        try:
            self._headerNames.append(self._shapeType)
            allColumns = self._headerNames
            insertValue = []
            #'''
            import arcpy  
            with arcpy.da.InsertCursor(self._settings.OutputFileName, allColumns) as cursor:
            #'''
                for row in rows:
                        
                    insertValues = row.NonShapeValues(allColumns)
                    if self._shapeType == "SHAPE@XY":
                        insertValues.append(self.CreatePoint(row.PointValues()))
                    else: #It is a WKT
                        #insertValues.append(self.CreateShape("POLYGON ((-90.399653999999998 46.565288000000002, -90.178072 46.505119000000001, -90.113929999999996 46.348367000000003, -88.714465000000004 46.029463999999997, -88.212990000000005 45.968702999999998, -88.003071000000006 45.773822000000003, -87.798981999999995 45.672049999999999, -87.775658000000007 45.447499999999998, -87.694022000000004 45.246690999999998, -87.606555999999998 45.078119000000001, -88.020563999999993 44.606786, -87.927266000000003 44.452981000000001, -87.682360000000003 43.736876000000002, -87.909773000000001 43.220672, -87.804812999999996 42.317492000000001, -87.699853000000004 41.988953000000002, -87.542412999999996 41.737079000000001, -87.326662999999996 41.619487999999997, -86.778538999999995 41.789271999999997, -86.498645999999994 42.066918999999999, -86.294556999999998 42.472521, -86.218753000000007 42.931038000000001, -86.411179000000004 43.360736000000003, -86.539463999999995 43.639896, -86.417010000000005 43.875746999999997, -86.510307999999995 44.043641999999998, -86.355842999999993 44.250629000000004, -86.23339 44.517336, -86.256714000000002 44.683411, -86.064288000000005 44.766269999999999, -86.046794000000006 44.915118, -85.790226000000004 44.952269999999999, -85.591967999999994 45.154119000000001, -84.833924999999994 45.453512000000003, -83.900948 45.502575999999998, -83.253696000000005 45.059462000000003, -83.312006999999994 44.317419999999998, -83.772664000000006 44.003683000000002, -83.941766000000001 43.717785999999997, -83.667704000000001 43.591219000000002, -83.405304999999998 43.844085999999997, -82.956310000000002 44.074942999999998, -82.635598999999999 43.907136000000001, -82.431510000000003 43.056727000000002, -82.227422000000004 43.082286000000003, -81.941698000000002 43.243909000000002, -81.720116000000004 43.464385999999998, -83.113748999999999 42.151142999999998, -82.991296000000006 41.800007999999998, -81.568506999999997 41.595429000000003, -80.169042000000005 42.112276999999999, -78.876506000000006 42.766927000000003, -78.612137000000004 43.331395000000001, -76.924018000000004 43.402537000000002, -76.116657000000004 43.615465, -76.312381000000002 44.109374000000003, -75.015709999999999 44.998474999999999, -71.492679999999993 45.102181999999999, -70.562990999999997 45.566536999999997, -70.220473999999996 46.213624000000003, -69.706699 47.003545000000003, -69.290785999999997 47.419024999999998, -68.948268999999996 47.236615, -68.361097000000001 47.385907000000003, -67.724995000000007 47.070241000000003, -67.700529000000003 45.720475999999998, -67.431409000000002 45.532271000000001, -67.406942999999998 45.153964999999999, -67.137822999999997 45.136709000000003, -66.917634000000007 44.651426999999998, -69.462044000000006 43.862931000000003, -70.342802000000006 43.455840000000002, -70.758714999999995 42.597372999999997, -71.101231999999996 42.218021999999998, -70.660853000000003 42.072902999999997, -70.391733000000002 41.836376999999999, -69.951353999999995 42.072902999999997, -69.902422999999999 41.470778000000003, -71.272490000000005 41.415759000000001, -72.055385999999999 41.139966000000001, -73.009540000000001 40.566302999999998, -73.865831999999997 40.473312, -76.268414000000007 36.704436000000001, -75.803569999999993 35.618085000000001, -76.341811000000007 34.818604999999998, -77.785274999999999 34.051841000000003, -79.179806999999997 33.278078000000001, -80.770064000000005 31.855457999999999, -81.357236 30.452736000000002, -80.647737000000006 28.579325999999998, -80.060564999999997 27.108346999999998, -80.036100000000005 25.794132999999999, -80.378615999999994 25.242165, -81.048236000000003 25.261022000000001, -82.149182999999994 26.646850000000001, -82.785285000000002 27.583226, -82.638491999999999 28.576150999999999, -82.981009 29.197367, -84.179817999999997 30.153897000000001, -85.109506999999994 29.644880000000001, -86.234919000000005 30.280743999999999, -88.192158000000006 30.344107000000001, -89.366501999999997 30.259615, -90.198328000000004 30.238479999999999, -89.366501999999997 29.474630999999999, -88.975054 29.197367, -90.907826999999997 29.346757, -92.131101999999998 29.708649000000001, -94.381927000000005 29.751138999999998, -95.629666999999998 28.983574000000001, -96.852941000000001 28.059248, -97.268854000000005 27.170445000000001, -97.024198999999996 25.856943999999999, -97.586905999999999 25.061726, -99.544145 26.821650999999999, -101.06100499999999 29.495927999999999, -101.84261100000001 29.772658, -102.601041 29.857565999999998, -103.04142 29.133557, -103.824315 29.347038000000001, -104.925262 30.618479000000001, -106.393191 31.66544, -108.154707 31.748695999999999, -108.08131 31.477841999999999, -111.017169 31.289867000000001, -114.711457 32.494619, -114.711457 32.721319000000001, -117.231403 32.638947999999999, -118.503608 33.988276999999997, -120.55870899999999 34.594659999999998, -121.09695000000001 35.595517000000001, -123.255814 38.661186999999998, -123.696192 39.118212999999997, -124.185502 40.135738000000003, -124.35676100000001 40.545985999999999, -124.30783 42.071213999999998, -124.699277 43.062202999999997, -123.935367 45.889242000000003, -124.791659 48.222230000000003, -123.15247100000001 48.205928, -123.22586800000001 49.09487, -95.171267 49.042817999999997, -94.119251000000006 48.737181, -92.259873999999996 48.397196999999998, -90.327100999999999 48.022207999999999, -89.593136000000001 48.054924999999997, -91.599305999999999 46.980983999999999, -91.207858000000002 46.830550000000002, -90.399653999999998 46.565288000000002))"))
                        insertValues.append(self.CreateShape(row.WKTValue()))
                    cursor.insertRow(insertValues)
        except Exception as ex:
            test = ex.message
            # Report that an error occurred
            arcpy.AddError("The batch projection of the file failed." + ex.message)
        
            # REPORT all messages   
            arcpy.AddMessage(arcpy.GetMessages())     

    def CreatePoint(self,points):
        import arcpy
        vertex = arcpy.CreateObject("Point")
        vertex.X = points[1]
        vertex.Y = points[0]   
        return vertex

    def CreateShape(self,wkt):
        import arcpy
        shape = arcpy.FromWKT(wkt)
        return shape