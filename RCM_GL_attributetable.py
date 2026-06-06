import os
from osgeo import ogr
from datetime import datetime

# =========================================================
# USER INPUTS
# =========================================================
# put in folder containing shapefiles to fill
shapefile_folder = "/Users/sina/Desktop/eric_rignot_lab/4Sina/shapefiles_forthesispaper/test_run2/Slessor/"
# =========================================================
# HELPERS
# =========================================================

def format_date_yyyymmdd(date_string):
    """Converts a date string from YYYYMMDD format to MM/DD/YY format.
    
    Args:
        date_string (str): Date in YYYYMMDD format (e.g., '20200115').
    
    Returns:
        str: Formatted date in MM/DD/YY format (e.g., '01/15/20').
    """
    dt = datetime.strptime(date_string, "%Y%m%d")
    return f"{dt.month}/{dt.day}/{str(dt.year)[-2:]}"


def parse_gl_filename_from_shp(shapefile_path, glacier_name):
    """Parses a glacier shapefile filename and extracts acquisition metadata.
    
    Extracts sensor, track, dates, orbits, and timing information from the 
    standardized glacier filename format. Expected format includes multiple 
    date-time components separated by underscores.

    Args:
        shapefile_path (str): Full path to the shapefile.
        glacier_name (str): Name of the glacier for the attribute table.

    Raises:
        ValueError: If filename does not contain at least 15 parts separated by underscores.

    Returns:
        dict: Dictionary containing parsed attributes including Glac_Name, Sensor, 
              Track, Year, Date_1-4, Orbit_1-4, Time_s, and Filename.
    """
    base = os.path.splitext(os.path.basename(shapefile_path))[0]
    parts = base.split("_")

    if len(parts) < 15:
        raise ValueError(f"Bad filename: {base}")

    date_1 = parts[5]
    time_1, date_2 = parts[6].split("-")

    date_3 = parts[8]
    time_3, date_4 = parts[9].split("-")

    return {
        "Glac_Name": glacier_name,
        "Sensor": parts[1],
        "Track": int(parts[2]),
        "Year": int(date_1[:4]),

        # only one time column
        "Time_s": int(parts[14].replace("s", "")),

        "Date_1": format_date_yyyymmdd(date_1),
        "Orbit_1": int(parts[10]),

        "Date_2": format_date_yyyymmdd(date_2),
        "Orbit_2": int(parts[11]),

        "Date_3": format_date_yyyymmdd(date_3),
        "Orbit_3": int(parts[12]),

        "Date_4": format_date_yyyymmdd(date_4),
        "Orbit_4": int(parts[13]),

        "Filename": base,
    }


def delete_field_if_exists(layer, field_name):
    """Deletes a field from the vector layer if it exists.
    
    Args:
        layer: OGR layer object to delete field from.
        field_name (str): Name of the field to delete.
    """
    index = layer.FindFieldIndex(field_name, 1)
    if index != -1:
        layer.DeleteField(index)
        print(f"Deleted field: {field_name}")


def create_field_if_missing(layer, field_name, field_type, width=None):
    """Creates a new field in the vector layer if it doesn't already exist.
    
    Args:
        layer: OGR layer object to create field in.
        field_name (str): Name of the field to create.
        field_type: OGR field type (e.g., ogr.OFTInteger, ogr.OFTString).
        width (int, optional): Width for string fields. Defaults to None.
    """
    index = layer.FindFieldIndex(field_name, 1)

    if index == -1:
        field = ogr.FieldDefn(field_name, field_type)

        if width is not None:
            field.SetWidth(width)

        layer.CreateField(field)
        print(f"Created field: {field_name}")


def clean_and_create_fields(layer):
    """Removes unwanted fields and creates the desired attribute fields.
    
    Deletes legacy fields (id, Prefix, Time_1-3, Date_5, Orbit_5) and ensures
    all required fields exist with correct types for storing glacier acquisition metadata.
    
    Args:
        layer: OGR layer object to clean and configure.
    """

    # Delete unwanted old fields
    unwanted_fields = [
        "id",
        "Prefix",
        "Time_1",
        "Time_2",
        "Time_3",
        "Date_5",
        "Orbit_5",
    ]

    for field_name in unwanted_fields:
        delete_field_if_exists(layer, field_name)

    # Create desired fields
    create_field_if_missing(layer, "fid", ogr.OFTInteger)
    create_field_if_missing(layer, "Glac_Name", ogr.OFTString, 40)
    create_field_if_missing(layer, "Sensor", ogr.OFTString, 20)
    create_field_if_missing(layer, "Track", ogr.OFTInteger)
    create_field_if_missing(layer, "Year", ogr.OFTInteger)
    create_field_if_missing(layer, "Time_s", ogr.OFTInteger)

    create_field_if_missing(layer, "Date_1", ogr.OFTString, 20)
    create_field_if_missing(layer, "Orbit_1", ogr.OFTInteger)

    create_field_if_missing(layer, "Date_2", ogr.OFTString, 20)
    create_field_if_missing(layer, "Orbit_2", ogr.OFTInteger)

    create_field_if_missing(layer, "Date_3", ogr.OFTString, 20)
    create_field_if_missing(layer, "Orbit_3", ogr.OFTInteger)

    create_field_if_missing(layer, "Date_4", ogr.OFTString, 20)
    create_field_if_missing(layer, "Orbit_4", ogr.OFTInteger)

    create_field_if_missing(layer, "Filename", ogr.OFTString, 180)


def fill_shapefile(shapefile_path, glacier_name):
    """Populates shapefile attribute fields from filename metadata.
    
    Opens the shapefile, prepares fields, parses the filename to extract metadata,
    and assigns values to all features in the layer. Requires at least one feature
    to be present in the shapefile.

    Args:
        shapefile_path (str): Full path to the shapefile to populate.
        glacier_name (str): Name of the glacier to assign to all features.
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.Open(shapefile_path, 1)

    if datasource is None:
        print(f"Could not open: {shapefile_path}")
        return

    layer = datasource.GetLayer()

    clean_and_create_fields(layer)

    values = parse_gl_filename_from_shp(shapefile_path, glacier_name)

    if layer.GetFeatureCount() == 0:
        print(f"No features in {os.path.basename(shapefile_path)}")
        print("Draw line in QGIS and save first.")
        datasource = None
        return

    layer.ResetReading()

    for i, feature in enumerate(layer, start=1):
        feature.SetField("fid", i)

        for field_name, field_value in values.items():
            feature.SetField(field_name, field_value)

        layer.SetFeature(feature)

    datasource = None

    print(f"Filled: {os.path.basename(shapefile_path)}")


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    glacier_name = input("Enter glacier name, for example Slessor: ").strip()

    shapefiles = [
        os.path.join(shapefile_folder, f)
        for f in os.listdir(shapefile_folder)
        if f.startswith("gl_") and f.endswith(".shp")
    ]

    if not shapefiles:
        print("No shapefiles found.")
    else:
        for shp in shapefiles:
            try:
                fill_shapefile(shp, glacier_name)
            except Exception as e:
                print(f"Skipping {os.path.basename(shp)} because of error: {e}")
