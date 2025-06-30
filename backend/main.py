import os
from dotenv import load_dotenv
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_ai import Agent
from groq import Groq
from typing import Optional, List

load_dotenv()

class WeatherData(BaseModel) :
    temperature: float
    humidity: int
    city: str
    description: str
    icon: str

class ForecastDay(BaseModel):
    date: str
    temperature: float
    description: str
    icon: str

class Deps :
    def __init__(self) :
        self.weather_api_key = os.environ["WEATHER_API_KEY"]
        self.groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

def getWeatherData(deps: Deps, lat: float, lon: float) :
    url = f"http://api.weatherapi.com/v1/current.json?key={deps.weather_api_key}&q={lat},{lon}&aqi=no"
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            return None
            
        response.raise_for_status()  
        
        data = response.json()
        
        current = data['current']
        location = data['location']
        condition = current['condition']
        
        return WeatherData(
            temperature=current['temp_c'],
            humidity=current['humidity'],
            city=location['name'],
            description=condition['text'],
            icon=condition['icon']
        )
        
    except requests.exceptions.RequestException as e:
        return None
    except KeyError as e:
        return None

def getWeatherDataByCity(deps: Deps, city: str) :
    url = f"http://api.weatherapi.com/v1/current.json?key={deps.weather_api_key}&q={city}&aqi=no"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        
        data = response.json()
        current = data['current']
        location = data['location']
        condition = current['condition']
        
        return WeatherData(
            temperature=current['temp_c'],
            humidity=current['humidity'],
            city=location['name'],
            description=condition['text'],
            icon=condition['icon']
        )
        
    except requests.exceptions.RequestException as e:
        return None
    except KeyError as e:
        return None

weather_agent = Agent(
    model="groq:llama-3.3-70b-versatile",
    system_prompt="You must check the weather data provided by the function above and provide suggestions accordingly. return the output in html unordered list tags"
)


app = FastAPI(title="Clima - Weather & Suggestions ", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


deps = Deps()

@app.get("/")
async def root():
    return {"message": "Clima"}

@app.get("/weather")
async def get_weather(lat: Optional[float] = None, lon: Optional[float] = None):
    """Get current weather data and AI suggestions"""
    try:
        if lat is None or lon is None:
            raise HTTPException(status_code=400, detail="Latitude and longitude are required")
        
        weather_data = getWeatherData(deps, lat, lon)
        if not weather_data:
            raise HTTPException(status_code=500, detail="Could not fetch weather data")
        
        weather_info = f"Temperature: {weather_data.temperature}°C, Humidity: {weather_data.humidity}%, City: {weather_data.city}"
        ai_response = await weather_agent.run(weather_info)
        
        # Extract just the content, not the full AgentRunResult string
        if hasattr(ai_response, 'output'):
            ai_suggestions = ai_response.output
        else:
            # If it's a string, try to extract content after "output="
            response_str = str(ai_response)
            if 'output=' in response_str:
                # Extract content between quotes after "output="
                start = response_str.find('output="') + 8
                end = response_str.rfind('"')
                ai_suggestions = response_str[start:end] if start > 7 and end > start else response_str
            else:
                ai_suggestions = response_str
        
        return {
            "location": {"lat": lat, "lon": lon, "city": weather_data.city},
            "weather": weather_data.dict(),
            "suggestions": ai_suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/{lat}/{lon}")
async def get_weather_by_coordinates(lat: float, lon: float):
    """Get weather data for specific coordinates"""
    try:
        
        weather_data = getWeatherData(deps, lat, lon)
        if not weather_data:
            raise HTTPException(status_code=500, detail="Could not fetch weather data")
        
        
        weather_info = f"Temperature: {weather_data.temperature}°C, Humidity: {weather_data.humidity}%, City: {weather_data.city}"
        ai_response = await weather_agent.run(weather_info)
        
        # Extract just the content, not the full AgentRunResult string
        if hasattr(ai_response, 'output'):
            ai_suggestions = ai_response.output
        else:
            # If it's a string, try to extract content after "output="
            response_str = str(ai_response)
            if 'output=' in response_str:
                # Extract content between quotes after "output="
                start = response_str.find('output="') + 8
                end = response_str.rfind('"')
                ai_suggestions = response_str[start:end] if start > 7 and end > start else response_str
            else:
                ai_suggestions = response_str
        
        return {
            "weather": weather_data.dict(),
            "suggestions": ai_suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/weather/city/{city}")
async def get_weather_by_city(city: str):
    """Get weather data for a specific city"""
    try:
        # Get weather data using city name
        weather_data = getWeatherDataByCity(deps, city)
        if not weather_data:
            raise HTTPException(status_code=500, detail="Could not fetch weather data")
        
        # Generate AI suggestions
        weather_info = f"Temperature: {weather_data.temperature}°C, Humidity: {weather_data.humidity}%, City: {weather_data.city}"
        ai_response = await weather_agent.run(weather_info)
        
        # Extract just the content, not the full AgentRunResult string
        if hasattr(ai_response, 'output'):
            ai_suggestions = ai_response.output
        else:
            # If it's a string, try to extract content after "output="
            response_str = str(ai_response)
            if 'output=' in response_str:
                # Extract content between quotes after "output="
                start = response_str.find('output="') + 8
                end = response_str.rfind('"')
                ai_suggestions = response_str[start:end] if start > 7 and end > start else response_str
            else:
                ai_suggestions = response_str
        
        return {
            "weather": weather_data.dict(),
            "suggestions": ai_suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/location")
async def get_weather_from_browser_location(payload: dict):
    lat = payload.get("lat")
    lon = payload.get("lon")

    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Latitude and longitude required")

    try:
        weather_data = getWeatherData(deps, lat, lon)
        if not weather_data:
            raise HTTPException(status_code=500, detail="Could not fetch weather data")

        weather_info = f"Temperature: {weather_data.temperature}°C, Humidity: {weather_data.humidity}%, City: {weather_data.city}"
        ai_response = await weather_agent.run(weather_info)

        # extract suggestions like in other routes
        if hasattr(ai_response, 'output'):
            ai_suggestions = ai_response.output
        else:
            response_str = str(ai_response)
            if 'output=' in response_str:
                start = response_str.find('output="') + 8
                end = response_str.rfind('"')
                ai_suggestions = response_str[start:end] if start > 7 and end > start else response_str
            else:
                ai_suggestions = response_str

        return {
            "location": {"lat": lat, "lon": lon},
            "weather": weather_data.dict(),
            "suggestions": ai_suggestions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast")
async def get_forecast(lat: Optional[float] = None, lon: Optional[float] = None, city: Optional[str] = None):
    """Get 7-day weather forecast from weatherapi.com"""
    try:
        if city:
            q = city
        elif lat is not None and lon is not None:
            q = f"{lat},{lon}"
        else:
            raise HTTPException(status_code=400, detail="Latitude/longitude or city required")
        url = f"http://api.weatherapi.com/v1/forecast.json?key={deps.weather_api_key}&q={q}&days=7&aqi=no&alerts=no"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        forecast_days = data['forecast']['forecastday']
        forecast = []
        for day in forecast_days:
            forecast.append(ForecastDay(
                date=day['date'],
                temperature=day['day']['avgtemp_c'],
                description=day['day']['condition']['text'],
                icon=day['day']['condition']['icon']
            ))
        return {"forecast": [f.dict() for f in forecast]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)