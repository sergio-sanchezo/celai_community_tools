from typing import Any
from cel.assistants.common import Param
from celai_community_tools.tool import tool
from celai_community_tools.auth import OpenWeatherMap


def _import_dotenv() -> Any:
    """Import python-dotenv library."""
    try:
        from dotenv import load_dotenv
        return load_dotenv
    except ImportError as e:
        raise ImportError(
            "Cannot import dotenv, please install with `pip install python-dotenv`."
        ) from e


def _import_requests() -> Any:
    """Import requests library."""
    try:
        import requests
        return requests
    except ImportError as e:
        raise ImportError(
            "Cannot import requests, please install with `pip install requests`."
        ) from e


@tool(
    name="GetWeather",
    desc="Get current weather information for a location",
    requires_auth=OpenWeatherMap(),
    params=[
        Param(name="location", type="string", description="The location to get weather for (city name, zip code, etc.)", required=True),
        Param(name="units", type="string", description="The unit system to use (metric, imperial, standard). Defaults to metric.", required=False),
    ]
)
def get_weather(params, ctx):
    """
    Get current weather information for a location.
    
    Args:
        params: A dictionary containing the parameters (location, units)
        ctx: The function context
        
    Returns:
        A string containing weather information.
    """
    # Import required dependencies
    load_dotenv = _import_dotenv()
    requests = _import_requests()
    
    # Extract parameters from the params dict
    location = params.get("location")
    units = params.get("units", "metric")
    
    # Use the OPENWEATHER_API_KEY from environment variables or .env file
    import os
    load_dotenv()
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    
    if not api_key:
        return "Error: OPENWEATHER_API_KEY environment variable is required but not found."
    
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "q": location,
                "appid": api_key,
                "units": units,
            },
            timeout=30  # Set a reasonable timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Format the response for better readability
        weather_info = {
            "location": {
                "name": data.get("name", ""),
                "country": data.get("sys", {}).get("country", ""),
                "coordinates": {
                    "lat": data.get("coord", {}).get("lat", 0),
                    "lon": data.get("coord", {}).get("lon", 0),
                },
            },
            "weather": {
                "condition": data.get("weather", [{}])[0].get("main", ""),
                "description": data.get("weather", [{}])[0].get("description", ""),
                "temperature": {
                    "current": data.get("main", {}).get("temp", 0),
                    "feels_like": data.get("main", {}).get("feels_like", 0),
                    "min": data.get("main", {}).get("temp_min", 0),
                    "max": data.get("main", {}).get("temp_max", 0),
                },
                "humidity": data.get("main", {}).get("humidity", 0),
                "pressure": data.get("main", {}).get("pressure", 0),
                "wind": {
                    "speed": data.get("wind", {}).get("speed", 0),
                    "direction": data.get("wind", {}).get("deg", 0),
                },
                "clouds": data.get("clouds", {}).get("all", 0),
                "visibility": data.get("visibility", 0),
            },
            "units": units,
            "timestamp": data.get("dt", 0),
            "sunrise": data.get("sys", {}).get("sunrise", 0),
            "sunset": data.get("sys", {}).get("sunset", 0),
        }
        
        return str(weather_info)
    
    except Exception as e:
        return f"Error fetching weather information for {location}: {str(e)}"