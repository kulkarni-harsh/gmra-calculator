import logging

import httpx

from app.core.config import settings
from app.types.alphasophia import CPT, Provider


async def get_hcp_data(
    zip_codes_list: list[str],
    taxonomy_codes_list: list[str],
    cpt_codes_list: list[str],
    npi_list: list[str],
    page_size: int,
) -> list[Provider]:
    """ "Fetch healthcare provider data from the AlphaSophia API based on specified filters.

    Args
    ----
        zip_codes_list (list[str]): A list of ZIP codes to filter providers by location.
        taxonomy_codes_list (list[str]): A list of taxonomy codes to filter providers by specialty.
        cpt_codes_list (list[str]): A list of CPT codes to filter providers by procedures performed.
        npi_list (list[str]): A list of NPI numbers to filter providers by.
        page_size (int): The number of results to return per page.

    Returns
    -------
        list[Provider]: A list of Provider objects matching the specified filters.
    """
    try:
        url = "https://api.alphasophia.com/v1/search/hcp"
        params: dict[str, str | int] = {"order-by": "ap-volume", "time": "last-year", "view": "table", "target": "hcps"}
        if len(zip_codes_list) > 0:
            params["zip5"] = ", ".join([f"+{code}" for code in zip_codes_list])
        if len(taxonomy_codes_list) > 0:
            params["taxonomy"] = ", ".join([f"+{code}" for code in taxonomy_codes_list])
        if len(cpt_codes_list) > 0:
            params["procedure-all-payor"] = ", ".join([f"+{code}" for code in cpt_codes_list])
        if len(npi_list) > 0:
            params["npi"] = ", ".join([f"+{code}" for code in npi_list])
        if page_size:
            params["pageSize"] = page_size

        headers = {
            "x-api-key": settings.ALPHASOPHIA_API_KEY,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_dict = response.json()
        print(response_dict)
        providers_list = [Provider(**item) for item in response_dict.get("data", [])]

        return providers_list

    except httpx.RequestError as exc:
        logging.critical(f"An error occurred while requesting {exc.request.url!r}.", exc_info=True)
        raise
    except httpx.HTTPStatusError as exc:
        logging.critical(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise
    except Exception as exc:
        logging.critical(f"An unexpected error occurred. {type(exc).__name__}: {exc}", exc_info=True)
        raise


async def get_npi_address(npi: str | None) -> tuple[str | None, str | None, str | None]:
    """Fetch the address information for a given NPI number from the NPI Registry API.

    Args
    ---
        npi (str | None): The NPI number for which to fetch the address information.

    Returns
    -------
        tuple[str | None, str | None]: Address Line 1, 2 & Postal Code (9 digits)
    """
    if not npi:
        return None, None, None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://npiregistry.cms.hhs.gov/api/", params={"number": npi, "version": "2.1"}
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()

        address_list = data["results"][0]["addresses"]
        location_address_list = [address for address in address_list if address["address_purpose"] == "LOCATION"]

        if len(location_address_list) > 0:
            relevant_address = location_address_list[0]
        else:
            logging.critical(f"No LOCATION address found for NPI {npi}")
            return None, None, None
        return relevant_address.get("address_1"), relevant_address.get("address_2"), relevant_address.get("postal_code")
    except httpx.RequestError:
        logging.critical(f"An error occurred while requesting NPI Registry API for NPI {npi}.")
        return None, None, None
    except httpx.HTTPStatusError as exc:
        logging.critical(f"Error response {exc.response.status_code} while requesting NPI Registry API for NPI {npi}.")
        return None, None, None
    except Exception as exc:
        logging.critical(
            f"An unexpected error occurred while fetching NPI address for NPI {npi}. {type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return None, None, None


async def get_hcp_profile(hcp_id: int) -> str | None:
    """Fetch the display name of an HCP from the AlphaSophia profile API.

    Args
    ----
        hcp_id (int): The AlphaSophia HCP ID.

    Returns
    -------
        str | None: The provider's name, or None if unavailable.
    """
    try:
        url = "https://api.alphasophia.com/v1/profile/hcp/"
        headers = {
            "x-api-key": settings.ALPHASOPHIA_API_KEY,
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params={"id": hcp_id}, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
        return data.get("data", {}).get("name")
    except Exception as exc:
        logging.warning("Could not fetch HCP profile for id %s: %s", hcp_id, exc)
        return None


async def get_hcp_procedure(
    hcp_id: int,
    page: int,
    code: str | None = None,
) -> list[CPT]:
    # The API returns
    try:
        url = "https://api.alphasophia.com/v1/profile/hcp/procedure/"
        params = {"id": hcp_id, "all-payor": "true", "page": page, "pageSize": 15}
        if code:
            params["code"] = code
        headers = {
            "x-api-key": settings.ALPHASOPHIA_API_KEY,
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            response_dict = response.json()
            print(response_dict)

        cpt_code = [CPT(**cpt) for cpt in response_dict["data"]["procedures"]]
        return cpt_code
    except httpx.RequestError:
        logging.critical(f"An error occurred while requesting HCP Procedure API for HCP {hcp_id}.")
        return []
    except httpx.HTTPStatusError as exc:
        logging.critical(
            f"Error response {exc.response.status_code} while requesting HCP Procedure API for HCP {hcp_id}"
        )
        return []
    except Exception as exc:
        logging.critical(
            f"An unexpected error occurred while fetching HCP Procedure API"
            f" for HCP {hcp_id}. {type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return []
