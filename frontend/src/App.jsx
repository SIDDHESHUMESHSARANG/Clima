import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [weatherData, setWeatherData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [city, setCity] = useState('')

  const fetchWeather = async (customCity = null) => {
    setLoading(true)
    setError(null)
    
    try {
      let url
      if (customCity) {
        // For custom city search
        url = `${import.meta.env.VITE_CITY}/${encodeURIComponent(customCity)}`
        const response = await fetch(url)
        if (!response.ok) {
          throw new Error('Failed to fetch weather data')
        }
        const data = await response.json()
        setWeatherData(data)
      } else {
        // For geolocation-based weather
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              try {
                const response = await fetch(`${import.meta.env.VITE_WEATHER}/location`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                  })
                })
                
                if (!response.ok) {
                  throw new Error('Failed to fetch weather data')
                }
                
                const data = await response.json()
                setWeatherData(data)
              } catch (err) {
                setError(err.message)
              } finally {
                setLoading(false)
              }
            },
            (error) => {
              setError('Unable to get your location. Please try searching for a city.')
              setLoading(false)
            }
          )
        } else {
          setError('Geolocation is not supported by this browser.')
          setLoading(false)
        }
      }
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWeather()
  }, [])

  const handleCustomLocation = (e) => {
    e.preventDefault()
    if (city.trim()) {
      fetchWeather(city.trim())
    }
  }

  const getWeatherIcon = (temp) => {
    if (temp < 10) return '❄️'
    if (temp < 20) return '🌤️'
    if (temp < 30) return '☀️'
    return '🔥'
  }

  const getBackgroundClass = (temp) => {
    if (temp < 10) return 'cold'
    if (temp < 20) return 'cool'
    if (temp < 30) return 'warm'
    return 'hot'
  }

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading weather data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">
          <h2>⚠️ Error</h2>
          <p>{error}</p>
          <button onClick={() => fetchWeather()}>Try Again</button>
        </div>
      </div>
    )
  }

  return (
    <div className={`app ${weatherData?.weather ? getBackgroundClass(weatherData.weather.temperature) : ''}`}>
      <div className="container">
        <header>
          <h1>🌤️ Clima</h1>
          <p>Get personalized weather insights powered by AI</p>
        </header>

        {weatherData && (
          <div className="weather-card">
            <div className="location">
              <h2>{weatherData.weather?.city || weatherData.location?.city}</h2>
              {weatherData.location && (
                <p>📍 {weatherData.location.lat.toFixed(4)}, {weatherData.location.lon.toFixed(4)}</p>
              )}
            </div>

            <div className="weather-info">
              <div className="temperature">
                <span className="icon">{getWeatherIcon(weatherData.weather.temperature)}</span>
                <span className="temp">{weatherData.weather.temperature}°C</span>
              </div>
              
              <div className="details">
                <div className="detail">
                  <span className="label">Humidity</span>
                  <span className="value">💧 {weatherData.weather.humidity}%</span>
                </div>
              </div>
            </div>

            {weatherData.suggestions && (
              <div className="ai-suggestions">
                <h3>Suggestions</h3>
                <div className="suggestions-content">
                  {weatherData.suggestions.includes('<') ? (
                    <div dangerouslySetInnerHTML={{ __html: weatherData.suggestions }} />
                  ) : (
                    <ul style={{listStyle: 'none'}}>
                      {weatherData.suggestions
                        .split('\n')
                        .filter(line => line.trim())
                        .map((suggestion, index) => (
                          <li key={index}>{suggestion.trim()}</li>
                        ))}
                    </ul>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="custom-location">
          <h3>📍 Check Weather for Custom City</h3>
          <form onSubmit={handleCustomLocation}>
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter city name (e.g., Mumbai, London, New York)"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                required
              />
              <button type="submit">Get Weather</button>
            </div>
          </form>
        </div>

        <footer>
          <button onClick={() => fetchWeather()} className="refresh-btn">
            🔄 Refresh Current Location
          </button>
        </footer>
      </div>
    </div>
  )
}

export default App
