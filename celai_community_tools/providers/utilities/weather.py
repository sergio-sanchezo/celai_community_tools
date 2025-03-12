import json

import httpx
from cel.assistants.function_context import FunctionContext
from celai_community_tools.auth import OpenWeatherMap
from celai_community_tools.errors import ToolExecutionError
from celai_community_tools.tool import tool


@tool(
    name="GetWeather",
    desc="Get current weather information for a location",
    requires_auth=OpenWeatherMap(),
    requires_secrets=["OPENWEATHER_API_KEY"],
)
async def get_weather(
    context: FunctionContext,
    location: str,
    units: str = "metric",
) -> str:
    """
    Get current weather information for a location.
    
    Args:
        context: The function context containing authorization.
        location: The location to get weather for (city name, zip code, etc.).
        units: The unit system to use (metric, imperial, standard).
        
    Returns:
        A JSON string containing weather information.
    """
    api_key = context.get_secret("OPENWEATHER_API_KEY")
    if not api_key:
        raise ToolExecutionError(
            message="OpenWeather API key not found",
            developer_message="OPENWEATHER_API_KEY secret not provided",
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": location,
                    "appid": api_key,
                    "units": units,
                },
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
            
            return json.dumps(weather_info)
        
        except Exception as e:
            raise ToolExecutionError(
                message=f"Failed to get weather information: {str(e)}",
                developer_message=f"OpenWeather API error: {str(e)}",
            )