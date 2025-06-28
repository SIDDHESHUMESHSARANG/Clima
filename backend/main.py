import os
from dotenv import load_dotenv
import geocoder
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_ai import Agent
from groq import Groq

load_dotenv()

class WeatherData(BaseModel) :
    temperature: float
    humidity: int
    city: str

class Deps :
    def __init__(self) :
        self.weather_api_key = os.environ["WEATHER_API_KEY"]
        self.groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

def getUserLocation() :
    g = geocoder.ip('me')
    if g.ok :
        return {"lat": g.latlng[0], "lon": g.latlng[1], "city": g.city or "Unknown"}
    return None

def getWeatherData(deps: Deps, lat: float, lon: float) :
    url = f"http://api.weatherapi.com/v1/current.json?key={deps.weather_api_key}&q={lat},{lon}&aqi=no"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        
        data = response.json()
        
        
        current = data['current']
        location = data['location']
        
        return WeatherData(
            temperature=current['temp_c'],  
            humidity=current['humidity'],   
            city=location['name']          
        )
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None
    except KeyError as e:
        print(f"Error parsing weather data: {e}")
        return None

weather_agent = Agent(
    model="groq:llama-3.3-70b-versatile",
    system_prompt="You must check the weather data provided by the function above and provide suggestions accordingly. return the output in html unordered list tags"
)


app = FastAPI(title="Weather AI Assistant", version="1.0.0")


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
async def get_weather():
    """Get current weather data and AI suggestions"""
    try:
        
        location = getUserLocation()
        if not location:
            raise HTTPException(status_code=500, detail="Could not determine location")
        
        
        weather_data = getWeatherData(deps, location["lat"], location["lon"])
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
            "location": location,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)