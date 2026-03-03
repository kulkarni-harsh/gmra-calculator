import math
import os

import folium
import pandas as pd
from geopy.distance import geodesic  # Added for accurate geodesic calculations
from geopy.point import Point  # Added for point handling


def generate_map(
    df: pd.DataFrame,
    pointer_latitude: float,
    pointer_longitude: float,
    pointer_address_line_1: str,
    pointer_city: str,
    pointer_state: str,
    pointer_zip_code: str,
    circle_radius_miles: float = 0.5,
    html_filepath: str = "map.html",
) -> str:
    """Generate an interactive map with a circle and markers for hospitals within a specified radius.

    Args
    ----
        df (pd.DataFrame): DataFrame containing hospital data with latitude, longitude, and other relevant information.
        pointer_latitude (float): Latitude of the input location.
        pointer_longitude (float): Longitude of the input location.
        pointer_address_line_1 (str): Address line 1 of the input location for the popup.
        pointer_city (str): City of the input location for the popup.
        pointer_state (str): State of the input location for the popup.
        pointer_zip_code (str): Zip code of the input location for the popup.
        circle_radius_miles (float, optional): Radius of the circle in miles. Defaults to 0.5 miles.
        html_filepath (str, optional): File path to save the generated map HTML. Defaults to "map.html".

    Returns
    -------
        str: Absolute file path to the saved HTML map.
    """
    radius_meters = circle_radius_miles * 1609.344
    # Create map centered at the input location
    m = folium.Map(
        location=[pointer_latitude, pointer_longitude],
        zoom_control=False,
        attribution_control=False,
        tiles=["OpenStreetMap", "CartoDB Positron", "CartoDB Voyager"][0],
    )

    # 1. Add the circle
    folium.Circle(
        location=[pointer_latitude, pointer_longitude],
        radius=radius_meters,
        color="blue",
        fill=True,
        fill_opacity=0.2,
    ).add_to(m)

    # 1.5. Add radius line and label (horizontal to the east, using geopy for accuracy)
    center_point = Point(pointer_latitude, pointer_longitude)
    east_point = geodesic(meters=radius_meters).destination(center_point, 90)

    # Use the existing East point for your radius line to keep it horizontal
    end_lat, end_lon = east_point.latitude, east_point.longitude
    # Add the PolyLine for the radius (dashed for better visibility)
    folium.PolyLine(
        locations=[[pointer_latitude, pointer_longitude], [end_lat, end_lon]],
        color="blue",
        weight=3,  # Increased weight for better visibility
        dashArray="5,5",  # Dashed line for a cleaner look
    ).add_to(m)
    # Add a text label at the midpoint
    folium.Marker(
        location=[(pointer_latitude + end_lat) / 2, (pointer_longitude + end_lon) / 2],
        icon=folium.DivIcon(
            html=(
                '<div style="font-size: 20pt; color: blue; font-weight: bold;'
                f'text-align: center; white-space: nowrap;">{circle_radius_miles} miles</div>'
            )
        ),
    ).add_to(m)

    # 3. Add markers for each location in the DataFrame
    for _, row in df.iterrows():
        if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['Primary Practice First Line']}",
                tooltip=f"{row['Name']} - {row['distance_from_source_miles']:.2f} miles",
                icon=folium.Icon(
                    icon="hospital",
                    prefix="fa",
                    color="gray" if row["distance_from_source_miles"] > circle_radius_miles else "blue",
                ),
            ).add_to(m)

            # Add marker coordinate to our bounds list
            # if row["distance_from_source_miles"] <= circle_radius_miles:
            # all_coordinates.append([row["latitude"], row["longitude"]])

    # 4. Add red marker for the input address
    folium.Marker(
        location=[pointer_latitude, pointer_longitude],
        popup=f"{pointer_address_line_1}, {pointer_city}, {pointer_state} {pointer_zip_code}",
        icon=folium.Icon(
            icon="anchor",
            prefix="fa",
            color="darkred",
        ),
        tooltip=f"{pointer_address_line_1}, {pointer_city}, {pointer_state} {pointer_zip_code}",
        z_index_offset=1000,  # Ensures this marker renders on top of others
    ).add_to(m)

    if circle_radius_miles <= 5:
        tightness = 0.95  # Minimal shrink for small circles
    elif circle_radius_miles <= 12:
        tightness = 0.90  # Moderate shrink
    else:
        tightness = 0.82  # Aggressive shrink for 13-20mi to prevent "Super Zoom Out"

    # 3. Coordinate Math
    # 1 degree lat ≈ 69 miles
    lat_deg_per_mi = 1 / 69.0
    # Longitude degrees "shrink" as you move away from the equator
    lon_deg_per_mi = 1 / (69.0 * math.cos(math.radians(pointer_latitude)))

    # Calculate the offsets with the tightness factor applied
    lat_offset = (circle_radius_miles * lat_deg_per_mi) * tightness
    lon_offset = (circle_radius_miles * lon_deg_per_mi) * tightness
    # Define the bounding box [SouthWest, NorthEast]
    sw = [pointer_latitude - lat_offset, pointer_longitude - lon_offset]
    ne = [pointer_latitude + lat_offset, pointer_longitude + lon_offset]
    m.fit_bounds([sw, ne], padding=(1, 1))

    # Save the map to an HTML file and return its absolute path
    m.save(html_filepath)

    return os.path.abspath(html_filepath)
