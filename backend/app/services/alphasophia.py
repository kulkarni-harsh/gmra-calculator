import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.types.alphasophia import CPT, Provider

_HCP_SEARCH_TIMEOUT = httpx.Timeout(connect=10, read=60, write=10, pool=10)
_NPI_TIMEOUT = httpx.Timeout(connect=10, read=30, write=10, pool=10)
_PROCEDURE_TIMEOUT = httpx.Timeout(connect=10, read=60, write=10, pool=10)


@retry(
    retry=retry_if_exception_type(httpx.TimeoutException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _fetch_hcp_data(
    zip_codes_list: list[str],
    taxonomy_codes_list: list[str],
    cpt_codes_list: list[str],
    npi_list: list[str],
    page_size: int,
) -> list[Provider]:
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
        response = await client.get(url, params=params, headers=headers, timeout=_HCP_SEARCH_TIMEOUT)
        response.raise_for_status()
        response_dict = response.json()

    return [Provider(**item) for item in response_dict.get("data", [])]


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
        return await _fetch_hcp_data(zip_codes_list, taxonomy_codes_list, cpt_codes_list, npi_list, page_size)
    except httpx.TimeoutException as e:
        logging.critical(f"Timed out requesting AlphaSophia HCP search API after 3 attempts. {type(e).__name__}: {e}")
        raise
    except httpx.RequestError as exc:
        logging.critical(f"An error occurred while requesting {exc.request.url!r}.", exc_info=True)
        raise
    except httpx.HTTPStatusError as exc:
        logging.critical(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
        raise
    except Exception as exc:
        logging.critical(f"An unexpected error occurred. {type(exc).__name__}: {exc}", exc_info=True)
        raise


@retry(
    retry=retry_if_exception_type(httpx.TimeoutException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _fetch_npi_address(npi: str) -> tuple[str | None, str | None, str | None]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://npiregistry.cms.hhs.gov/api/",
            params={"number": npi, "version": "2.1"},
            timeout=_NPI_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

    address_list = data["results"][0]["addresses"]
    location_address_list = [address for address in address_list if address["address_purpose"] == "LOCATION"]

    if len(location_address_list) > 0:
        relevant_address = location_address_list[0]
    else:
        logging.critical(f"No LOCATION address found for NPI {npi}")
        return None, None, None
    return relevant_address.get("address_1"), relevant_address.get("address_2"), relevant_address.get("postal_code")


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
        return await _fetch_npi_address(npi)
    except httpx.TimeoutException as e:
        logging.critical(f"Timed out requesting NPI API for {npi} after 3 attempts. {type(e).__name__}: {e}")
        return None, None, None
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


@retry(
    retry=retry_if_exception_type(httpx.TimeoutException),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _fetch_hcp_procedure(hcp_id: int, page: int, code: str | None) -> list[CPT]:
    url = "https://api.alphasophia.com/v1/profile/hcp/procedure/"
    params: dict[str, str | int | bool] = {"id": hcp_id, "all-payor": "true", "page": page, "pageSize": 15}
    if code:
        params["code"] = code
    headers = {
        "x-api-key": settings.ALPHASOPHIA_API_KEY,
        "Accept": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers, timeout=_PROCEDURE_TIMEOUT)
        response.raise_for_status()
        response_dict = response.json()
    return [CPT(**cpt) for cpt in response_dict["data"]["procedures"]]


async def get_hcp_procedure(
    hcp_id: int,
    page: int,
    code: str | None = None,
) -> list[CPT]:
    try:
        return await _fetch_hcp_procedure(hcp_id, page, code)
    except httpx.TimeoutException as e:
        logging.critical(
            f"Timed out requesting HCP Procedure API for HCP {hcp_id}: {code} after 3 attempts. {type(e).__name__}: {e}"
        )
        return []
    except httpx.RequestError as e:
        logging.critical(
            f"An error occurred while requesting HCP Procedure API for HCP {hcp_id}: {code}. {type(e).__name__}: {e}"
        )
        return []
    except httpx.HTTPStatusError as exc:
        logging.critical(
            f"Error response {exc.response.status_code} while requesting HCP Procedure API for HCP {hcp_id}: {code}"
        )
        return []
    except Exception as exc:
        logging.critical(
            f"Unexpected error occurred while fetching Procedure for HCP {hcp_id}: {code}. {type(exc).__name__}: {exc}",
            exc_info=True,
        )
        return []
