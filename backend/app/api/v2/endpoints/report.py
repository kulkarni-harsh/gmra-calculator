from fastapi import APIRouter, Request
import pandas as pd

from app.schemas.provider_request import ProviderRequest
from app.services.mapbox import get_drive_distance_time, get_location_coordinates

router = APIRouter()


@router.post("/generate")
def generate_report(
    payload: ProviderRequest,
    request: Request
):
    """
    Generate a report based on the provided provider information.

    This endpoint accepts a JSON payload containing provider details such as address, specialty, and service area radius. It processes the information to generate a comprehensive report that may include insights on nearby providers, service coverage, and other relevant data.

    Args
    ----
        payload (ProviderRequest): A Pydantic model containing the provider's address, specialty, and miles radius.

    Returns
    -------
        dict; A dictionary containing order ID, status, and a message indicating the result of the report generation process.
    """
    # Placeholder implementation for report generation logic
    # In a real implementation, this would involve processing the payload and generating the report

    # Convert input location to latitude and longitude using Mapbox
    input_latitude, input_longitude = get_location_coordinates(
        f"{payload.address_line_1}, {payload.address_line_2}, {payload.city}, {payload.state} {payload.zip_code}"
    )
    print(input_latitude, input_longitude)

    # TODO: Replace with API request to get nearby providers based on input location and specialty
    nearby_providers_df = pd.read_excel("/Users/kulkarni-harsh/Downloads/Frisco OB_GYN.xlsx")

    # Get ZIP code centroids DataFrame from app state
    zip_centroids_df = request.app.state.zip_centroids_df.copy()

    # Geocode nearby provider addresses to get their latitudes and longitudes
    nearby_providers_df[["latitude", "longitude"]] = nearby_providers_df.apply(
        lambda row: get_location_coordinates(
            address = (f"{row['Primary Practice First Line']}, "
                       f"{row['Primary Practice City']}, "
                       f"{row['Primary Practice State']}, "
                       f"{row['Primary Practice ZIP']}")

        )
    )

    # Calculate distances from input location to each provider
    nearby_providers_df[["distance_from_source_miles", "duration_from_source_minutes"]] = nearby_providers_df.progress_apply(
        lambda r: get_drive_distance_time(
            lat1=float(r["latitude"]),
            long1=float(r["longitude"]),
            lat2=input_latitude,
            long2=input_longitude,
        ),
        axis=1,
    )

    




    return {
        "order_id": "12345",
        "status": "success",
        "message": "Report generated successfully.",
    }
