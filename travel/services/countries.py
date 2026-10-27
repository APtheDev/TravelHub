
import requests


class CountryNotFound(Exception):
    pass


class CountriesServiceUnavailable(Exception):
    pass


def get_country_data(country_code):
    """Récupère les informations d'un pays avec GraphQL."""

    url = "https://countries.trevorblades.com/"

    query = """
    query GetCountry($code: ID!) {
        country(code: $code) {
            code
            name
            capital
            currency
            continent {
                name
            }
            languages {
                name
            }
        }
    }
    """

    try:
        response = requests.post(
            url,
            json={
                "query": query,
                "variables": {
                    "code": country_code.upper()
                }
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError) as error:
        raise CountriesServiceUnavailable(
            "Impossible de contacter Countries GraphQL."
        ) from error

    if data.get("errors"):
        raise CountriesServiceUnavailable(
            "La requête GraphQL a retourné une erreur."
        )

    country = (data.get("data") or {}).get("country")

    if country is None:
        raise CountryNotFound(
            "Pays introuvable."
        )

    return {
        "code": country["code"],
        "nom": country["name"],
        "capitale": country["capital"],
        "monnaie": country["currency"],
        "continent": country["continent"]["name"],
        "langues": [
            language["name"]
            for language in country["languages"]
        ]
    }
