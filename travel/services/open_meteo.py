import requests

class DestinationNotFound(Exception):
    pass

class MeteoNotAvailable(Exception):
    pass

def get_weather_data(city, country):
    
    try:
       
        url_geo = "https://geocoding-api.open-meteo.com/v1/search"

        reponse_geo = requests.get(
            url_geo,
            params={
                "name": f"{city}, {country}",
                "count": 1,
                "language": "en"
            },
            timeout=10
        ) 
        
        reponse_geo.raise_for_status()
        
        result_geo = reponse_geo.json().get("results",[])
        
        if not result_geo:
            raise DestinationNotFound(f"La Destination dans la ville de '{city}, et dans le pays {country}' est introuvable.")
        lieu = result_geo[0]
        
        latitude = lieu["latitude"]
        longitude = lieu["longitude"]
        
        url_meteo = "https://api.open-meteo.com/v1/forecast"
        
        response_meteo = requests.get(
            url_meteo,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m",
                    "precipitation",
                    "weathercode",
                    "windspeed_10m",
                ),
                "timezone": "auto"
                
            },
            timeout=10
        )
        response_meteo.raise_for_status()
        
        donnees_meteo = response_meteo.json()
        meteo = donnees_meteo.get("current")
        
        if not meteo:
            raise MeteoNotAvailable(f"Les données météorologiques pour la ville de '{city},dans le pays {country}' ne sont pas disponibles.")
        
        return {
            "ville": lieu["name"],
            "pays": lieu["country"],
            "latitude": latitude,
            "longitude": longitude,
            "meteo_actuelle": meteo,
            "unites": donnees_meteo.get("current_units", {}),
        }
        
    except (requests.RequestException, ValueError, KeyError) as erreur:
        raise MeteoNotAvailable(
            "Impossible de récupérer les données Open-Meteo."
        ) from erreur

def get_country_code(city, country):
    """Récupère le code ISO du pays d'une destination."""

    url = "https://geocoding-api.open-meteo.com/v1/search"

    try:
        response = requests.get(
            url,
            params={
                "name": f"{city}, {country}",
                "count": 1,
                "language": "en"
            },
            timeout=10
        )

        response.raise_for_status()

        results = response.json().get("results", [])

    except (requests.RequestException, ValueError) as error:
        raise MeteoNotAvailable(
            "Le service de géocodage est indisponible."
        ) from error

    if not results:
        raise DestinationNotFound(
            "Impossible de trouver cette destination."
        )

    country_code = results[0].get("country_code")

    if not country_code:
        raise DestinationNotFound(
            "Le code du pays est introuvable."
        )

    return country_code
