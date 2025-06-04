# St. Louis River Estuary Habitat Mapping: Post-processing of initial UNET land cover classes

## Objectives and Rules

The objective of UNET "Phase 2" post-processing was to refine UNET-derived land cover classes using GIS-based rules and ancillary datasets. Input to the post-processing steps was a completed UNET land cover map in raster format, derived from NAIP aerial imagery. The study area is a one-mile buffer around the St. Louis River estuary in the Duluth-Superior area.

The post-processing steps took the form of a series of 8 rulesets. Each ruleset was applied to the output from the previous step. The rules are as follows:

- <span>Ruleset 1 - Overlay LANDFIRE riparian zones on UNET map to differentiate between wetland and upland classes. Specifically: a) Any pixel classified as **Forest** on UNET was reclassified as **Forested Wetland** if it coincided with a LANDFIRE **Open Water** or **Riparian pixel**. Otherwise the pixel was reclassified as **Forested Upland**. b) Any pixel classified as **Scrub-Shrub** on UNET was reclassified as **Scrub-Shrub Wetland** if it coincided with a LANDFIRE **Open Water** or **Riparian** pixel. Otherwise the pixel was reclassified as **Scrub-Shrub Upland**. c) Any pixel classified as **Herbaceous** on UNET was reclassified as **Emergent Wetland** if it coincided with a LANDFIRE **Riparian** pixel, as **Aquatic Bed** if it coincided with a LANDFIRE **Open Water** pixel, and as **Herbaceous Upland** otherwise.</span>

- <span>Ruleset 2 - Overlay modified UNET map output by Ruleset 1 with wetlands polygons from Coastal Wetlands Monitoring Program (CWMP) for the St. Louis River Estuary. The goal was to modify some classes that were erroneously coded as upland by UNET. Ruleset 2 modifies 3 cases: a) Any pixel classified as **Forested Upland** was reclassified as **Forested Wetland** if it coincided with a CWMP **Wetlands** pixel. b) Any pixel classified as **Scrub-Shrub Upland** was reclassified as **Scrub-Shrub Wetland** if it coincided with a CWMP **Wetlands** pixel. c) Any pixel classified as **Herbaceous Upland** was reclassified as **Emergent Wetland** if it coincided with a CWMP **Wetlands** pixel.</span>

- <span>Ruleset 3 - Overlay modified UNET map output by Ruleset 2 with a rasterized layer of lake polygons. The goal was to differentiate rivers from lakes. Ruleset 3 modifies 2 cases: a) Any pixel classified as **Water** was reclassified as **Lake** if it coincided with a lake pixel. b) Any pixel classified as **Water** was reclassified as **River** if it did not coincide with a lake pixel.</span>

- <span>Ruleset 4 - Overlay modified UNET map output by Ruleset 3 with a rasterized layer of lake bathymetry. The goal was to differentiate lake littoral (above 2.5 m depth) from lake limnetic (over 2.5 m depth). Ruleset 4 modifies 2 cases: a) Any pixel classified as **Lake** was reclassified as **Lake Littoral** if it was less than 2.5 m in depth. b) Any pixel classified as **Lake** was reclassified as **Lake Limnetic** if it was more than 2.5 m in depth.</span>

- <span>Ruleset 5 - Overlay modified UNET map output by Ruleset 4 with a rasterized layer of edits determined by ecological consultants. The goal was to surgically fix some incorrectly classfied areas. A polygon layer of fixes was created with codes indicting how the modified UNET map was to be changed (e.g., change cultural to river). Most of the edits involved then classes of **Cultural**, **River**, **Unconsolidated** and **Aquatic Bed**.</span>

- <span>Ruleset 6 - Overlay modified UNET map output by Ruleset 5 with a rasterized layer of different **Unconsolidated** classes. The goal was to differentiate between **Unconsolidated Lakeshore**, **Unconsolidated Riverbank** and **Unconsolidated Upland**. These rules were implemented using a rasterized version of a polygon layer showing the differentiation of these classes.</span>

- <span>Ruleset 7 - Overlay modified UNET map output by Ruleset 6 with a rasterized layer identifying fixes to **River**, **Lake Littoral** and **Lake Limnetic** pixels. These areas were identified by the ecological consultants. Chnages included reclassifying these classes to **Unconsolidated Upland**, **Rocky**, **Ponds**, **Herbaceous Upland**, **Forested Wetland**, **Forested Upland** and **Cultural**.</span>

- <span>Ruleset 8 - Overlay modified UNET map output by Ruleset 7 with a rasterized layer derived from a wetlands survey of the estuary. The rules changed some pixels from **Herbaceous Upland** to **Emergent Wetland** and **Aquatic Bed**.</span>

## GIS Methods

The rulesets described above were implemented in GIS using standard raster processing tools such as Reclassify and Raster Calculator. The output of each ruleset was used as the input to the next ruleset. The output of the final ruleset produced the final version of the Habitat Map. The GIS procedure is encompassed within the Python code below, which extracts the rules from a stand-alone Excel file. This Excel file is included in this GitHub repository. Alternately, users can also run the Raster Calculator and Reclassify commands interactively, using the steps described on each tab of the spreadsheet.

Note that the edits made in the Phase 2 part of the project are tailored to the specific conditions of the St. Louis River Estuary Habitat Mapping Project. While the general principles may apply elsewhere, different datasets and rules would need to be used in other study areas.

All data used to implement the rules are available on the geodata@wisconsin geoportal. The LUTs (Look Up Tables) included in this GitHub repository define the class associated with the numerical codes in the GIS layers.

## Imports and other Header Information
```python
import pandas as pd
import arcpy
from arcpy.sa import *
from arcgis.gis import GIS
import arcgis
import os
```

```
rulesPath = MANUALLY_INPUTTED_RULE_PATH

ruleSteps = pd.ExcelFile(rulesPath).sheet_names

aprx = arcpy.mp.ArcGISProject("CURRENT")

mapView = aprx.listMaps()[0]

layers = mapView.listLayers()

rasters = {layer.name: Raster(arcpy.Describe(layer).catalogPath) 
           for layer in layers if layer.isRasterLayer}

arcpy.env.mask = rasters['unet']

outputPath = MANUALLY_INPUTTED_OUTPUT_PATH
```
## Functions

```python
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
    
def calculate(init, inter, step):
    firstRasterSize = int(
        arcpy.GetRasterProperties_management(
            init, 
            "MAXIMUM").getOutput(0))
    
    secondRasterSize = int(
        arcpy.GetRasterProperties_management(
            inter, 
            "MAXIMUM").getOutput(0))
    
    reclassPath = os.path.join(outputPath, 'rasterCalc' + str(step) + '.tif')
    
    if firstRasterSize > secondRasterSize:
        (inter * (10**int(math.ceil(math.log10(firstRasterSize)))) 
         + init).save(reclassPath)
        
        return reclassPath, inter, init, firstRasterSize # smaller, larger
    else:
        (init * (10**int(math.ceil(math.log10(secondRasterSize)))) 
         + inter).save(reclassPath)
        
        return reclassPath, init, inter, secondRasterSize # smaller, larger
        
def reclassify(df, toReclass, codes, larger, step):
    remapValues = 0

    scalingFactor = 10**int(math.ceil(math.log10(larger)))

    remapValues = RemapValue(
        [[row[codes[0]] * scalingFactor + row[codes[1]], 
          row[codes[2]]] 
         for index, row in df.iterrows()]
    )
    
    reclassifiedPath = os.path.join(outputPath, 'reclassified' + str(step) + '.tif')
    
    Reclassify(os.path.join(outputPath, 'rasterCalc' + str(step) + '.tif'),
           "VALUE",
           RemapValue([[row[codes[0]] * scalingFactor + row[codes[1]], 
                        row[codes[2]]] for index, row in df.iterrows()])).save(
                reclassifiedPath
           )
    
    return reclassifiedPath

def stratify(rules, currStep = 0, reclassifiedPath = None):
    step, drop, init, inter, operation = rules[currStep].split('-')
    
    stepNum = int(step[-1]) # for example, get last character of string 'step1'

    codes = [init.upper() + 'code', #INIT_NAMEcode
             inter.upper() + 'code', #INTER_NAMEcode
             init.upper()[:-1] + str(stepNum + 1) + 'code' if len(init) == 5
             else init.upper() + str(stepNum + 1) + 'code'] #INIT_NAME2Acode or INIT_NAME2code
    
    df = ingestRules(rulesPath, rules[stepNum - 1], codes)
    
    print(df)
    
    toReclass, smaller, larger, largerNum = calculate(rasters[init] if currStep == 0
                                                      else rasters[reclassifiedPath], 
                                                      rasters[inter],
                                                      stepNum)
        
    reclassifiedPath = reclassify(df, toReclass, codes, largerNum, stepNum)
    
    return reclassifiedPath
```
## Execution
Execute functions in pattern
```python
step1 = stratify(ruleSteps)

arcpy.management.MakeRasterLayer(os.path.join(outputPath, 'reclassified1.tif'), 'reclassified1')

layers = mapView.listLayers()

rasters = {layer.name: Raster(arcpy.Describe(layer).catalogPath) 
           for layer in layers if layer.isRasterLayer}

step2 = stratify(ruleSteps, 1, 'reclassified1')
```
For systems with greater computing power, alternative recursive functions can be written.

## Acknowledgements

This work was sponsored by the National Estuarine Research Reserve System Science Collaborative, which supports collaborative research that addresses coastal management problems important to the reserves. The Science Collaborative is funded by the National Oceanic and Atmospheric Administration and managed by the University of Michigan Water Center (NA19NOS4190058). The project team is also grateful for the support and assistance provided by the St. Louis River Habitat Workgroup.

