import pandas as pd
import arcpy
from arcpy.sa import *
from arcgis.gis import GIS
import arcgis
import os
import time

def ingestRules(rulesPath, ruleStep, ruleColumns):
    try:
        df = pd.read_excel(rulesPath, sheet_name = ruleStep, usecols = ruleColumns)
        return df
    except FileNotFoundError:
        print(f'Error: File not found at {rulesPath}')
        return None
    except ValueError:
        print(f'Error: One or more column names are invalid in the Rules file')
        return None
    except Exception as e:
        print(f'An unexpected error occured: {e}')
        return None

rulesPath = r'Z:\PROJECTS\Lake_Superior_NERR\final_habitat_map_spring2025\phase2-rules.xlsx'

ruleSteps = pd.ExcelFile(rulesPath).sheet_names

ruleSteps

aprx = arcpy.mp.ArcGISProject("CURRENT")

mapView = aprx.listMaps()[0]

layers = mapView.listLayers()

for layer in layers:
    if layer.isRasterLayer:
        print(f'Raster layer found: {layer.name}')

rasters = {layer.name: Raster(arcpy.Describe(layer).catalogPath) 
           for layer in layers if layer.isRasterLayer}

rasters

progressFilePath = r'C:\Users\scostaff_1\Documents\ArcGIS\Projects\MyProject\progressFile.txt'

if os.path.exists(progressFilePath):
    with open(progressFilePath, 'r') as f:
        index = f.read().strip()
        if (index == ''):
            lastProcessedRow = -1
        else:
            lastProcessedRow = int(index)

lastProcessedRow

rasters['unet'].height

rasters['unet'].width

rasterChunk = ExtractByRectangle(rasters['unet'], arcpy.Extent(0, 0, 2000, 2000))

for index, row in df.iloc[0:5].iterrows():
    print(row['UNETcode'])

testPath = r'C:\Users\scostaff_1\Documents\ArcGIS\Projects\MyProject\Classifications'

result = None

start = time.time()

for index, row in df.iloc[0:20].iterrows():
    result = Con((rasters['unet'] == row['UNETcode']) 
                 & (rasters['landfire'] == row['LANDFIREcode']), 
                 row['UNET2code'], result)
    print(f'Wrote conditions for {index} row')

diff = time.time() - start    

print(f'{diff} seconds to finish building conditional expression')

start_two = time.time()

result.save(os.path.join(testPath, 'CombinedTest1.tif'))

diff_two = time.time() - start_two

print(f'{diff_two} seconds to save')

result = None

start = time.time()

for index, row in df.iloc[0:5].iterrows():
    result = Con((rasters['unet'] == row['UNETcode']) 
                 & (rasters['landfire'] == row['LANDFIREcode']), 
                 row['UNET2code'], result)
    print(f'Wrote conditions for {index} row')
    
diff = time.time() - start    

print(f'{diff} seconds to finish conditional')

result.save(os.path.join(testPath, 'CombinedTest1.tif'))

diff = time.time() - diff

print(f'{diff} seconds to save')

result = None

start = time.time()

for index, row in df.iloc[0:10].iterrows():
    result = Con((rasters['unet'] == row['UNETcode']) 
                 & (rasters['landfire'] == row['LANDFIREcode']), 
                 row['UNET2code'], result)
    print(f'Wrote conditions for {index} row')
    
diff = time.time() - start    

print(f'{diff} seconds to finish conditional')

result.save(os.path.join(testPath, 'CombinedTest1.tif'))

diff = time.time() - diff

print(f'{diff} seconds to save')

testRasterPaths = [os.path.join(testPath, path) for 
                   path in os.listdir(testPath) 
                   if os.path.splitext(path)[-1].lower() == '.tif']

arcpy.management.MosaicToNewRaster(input_rasters = [testRasterPaths[0], 
                                                    testRasterPaths[1]], 
                                   ouput_location = testPath, 
                                   raster_dataset_name_with_extension = 'combinedTest0.tif', 
                                   number_of_bands = 1)

arcpy.env.mask = rasters['unet']

columns = ['UNETcode', 'LANDFIREcode', 'UNET2code', 'UNET2desc']

df = ingestRules(rulesPath, ruleSteps[0], columns)

(rasters['unet'] * 10000 + rasters['landfire']).save(os.path.join(testPath, 'rasterCalcTest.tif'))

Reclassify(os.path.join(testPath, 'rasterCalcTest.tif'),
           "VALUE",
           RemapValue([[row['UNETcode'] * 10000 + row['LANDFIREcode'], row['UNET2code']] for index, row in df.iterrows()])).save(
               os.path.join(testPath, 'reclassifiedTest.tif')
           )

columns = ['UNET2code', 'CWMPcode', 'UNET3code', 'UNET3desc']

df = ingestRules(rulesPath, ruleSteps[1], columns)

(rasters['reclassifiedTest.tif'] * 10 + rasters['cwmp_wetlands_reclass']).save(os.path.join(testPath, 'rasterCalc2Test.tif'))

Reclassify(os.path.join(testPath, 'rasterCalc2Test.tif'),
           "VALUE",
           RemapValue([[row['UNET2code'] * 10 + row['CWMPcode'], row['UNET3code']] for index, row in df.iterrows()])).save(
               os.path.join(testPath, 'reclassified2Test.tif')
           )

columns = ['UNET3code', 'LAKEcode', 'UNET4code', 'UNET4desc']

df = ingestRules(rulesPath, ruleSteps[2], columns)

(rasters['reclassified2Test.tif'] * 10 + rasters['lake']).save(os.path.join(testPath, 'rasterCalc3Test.tif'))

Reclassify(os.path.join(testPath, 'rasterCalc3Test.tif'),
           "VALUE",
           RemapValue([[row['UNET3code'] * 10 + row['LAKEcode'], row['UNET4code']] for index, row in df.iterrows()])).save(
               os.path.join(testPath, 'reclassified3Test.tif')
           )

columns = ['UNET4code', 'BATHcode', 'UNET5code', 'UNET5desc']

df = ingestRules(rulesPath, ruleSteps[3], columns)

(rasters['reclassified3Test.tif'] * 10 + rasters['bath']).save(os.path.join(testPath, 'rasterCalc4Test.tif'))

Reclassify(os.path.join(testPath, 'rasterCalc4Test.tif'),
           "VALUE",
           RemapValue([[row['UNET4code'] * 10 + row['BATHcode'], row['UNET5code']] for index, row in df.iterrows()])).save(
               os.path.join(testPath, 'reclassified4Test.tif')
           )

habitat_map_gdb = r'Z:\PROJECTS\Lake_Superior_NERR\final_habitat_map_spring2025\data\habitat-map.gdb'

newRulesPath = r'Z:\PROJECTS\Lake_Superior_NERR\final_habitat_map_spring2025\phase2-rules-new-version.xlsx'

newRulesSteps = pd.ExcelFile(newRulesPath).sheet_names

def stratify(rulePath, rule):
    df = ingestRules(rulePath, rule, inputAndTarget)
    # create gdb called outputs

df = ingestRules(newRulesPath, newRulesSteps[0], ['UNETcode', 'LANDFIREcode', 'UNET2Acode'])

firstRasterSize = int(
    arcpy.GetRasterProperties_management(
        landfire, 
        "MAXIMUM").getOutput(0))

secondRasterSize = int(
    arcpy.GetRasterProperties_management(
        unet, 
        "MAXIMUM").getOutput(0))

firstRasterSize, secondRasterSize

result = 0

if firstRasterSize > secondRasterSize:
    result = unet * (10**int(math.ceil(math.log10(firstRasterSize)))) + landfire
else:
    result = landfire * (10**int(math.ceil(math.log10(secondRasterSize)))) + unet

remapValues = 0

if firstRasterSize > secondRasterSize:
    scalingFactor = 10**int(math.ceil(math.log10(firstRasterSize)))
    
    remapValues = RemapValue(
        [[row['UNETcode'] * scalingFactor + row['LANDFIREcode'], 
          row['UNET2Acode']] 
         for index, row in df.iterrows()]
    )
else:
    scalingFactor = 10**int(math.ceil(math.log10(secondRasterSize)))
    
    remapValues = RemapValue(
        [[row['UNETcode'] * scalingFactor + row['LANDFIREcode'], 
          row['UNET2Acode']] 
         for index, row in df.iterrows()]
    )

remapValues

newRulesSteps

arcpy.env.workspace = habitat_map_gdb

# List raster datasets
rasters = arcpy.ListRasters()

for raster in rasters:
    print(f"Raster: {raster}")

rasters[0]


