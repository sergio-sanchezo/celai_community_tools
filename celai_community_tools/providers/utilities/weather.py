import json
import os
from typing import Any, Dict, List, Optional

from cel.assistants.common import Param
from cel.assistants.function_context import FunctionContext
from cel.assistants.function_response import FunctionResponse
from celai_community_tools.tool import tool

# Import httpx library
try:
    import httpx
except ImportError:
    # Create a fallback for documentation/development without the actual dependency
    class httpx:
        class AsyncClient:
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, *args):
                pass
                
            async def get(self, *args, **kwargs):
                return {"error": "httpx not installed"}


@tool(
    name="GetWeather",
    desc="Get current weather information for a location",
    requires_secrets=["OPENWEATHER_API_KEY"],
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
    # Extract parameters from the params dict
    location = params.get("location")
    units = params.get("units", "metric")
    
    # Use the OPENWEATHER_API_KEY from environment variables or .env file
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    
    if not api_key:
        return "Error: OPENWEATHER_API_KEY environment variable is required but not found."
    
    try:
        # Use synchronous request instead of async since the Firecrawl pattern is synchronous
        import requests
        
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