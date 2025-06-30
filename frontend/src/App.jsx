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
        url = `${import.meta.env.VITE_CITY}/${encodeURIComponent(customCity)}`
        const response = await fetch(url)
        if (!response.ok) throw new Error('Failed to fetch weather data')
        const data = await response.json()
        setWeatherData(data)
      } else {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            async (position) => {
              try {
                url = `${import.meta.env.VITE_WEATHER}/location`
                const response = await fetch(url, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ lat: position.coords.latitude, lon: position.coords.longitude })
                })
                if (!response.ok) throw new Error('Failed to fetch weather data')
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

  const getWeatherIcon = (description) => {
    if (!description) return '🌤️' // Fallback if description is undefined
    const desc = description.toLowerCase()
    if (desc.includes('rain') || desc.includes('drizzle')) return '🌧️'
    if (desc.includes('snow')) return '❄️'
    if (desc.includes('cloud') || desc.includes('overcast')) return '☁️'
    if (desc.includes('mist') || desc.includes('fog') || desc.includes('haze')) return '🌫️'
    if (desc.includes('thunder') || desc.includes('storm')) return '⛈️'
    if (desc.includes('clear')) return '☀️'
    if (desc.includes('partly')) return '⛅'
    if (desc.includes('scattered')) return '🌤️'
    return '🌤️'
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
          <img src="/loading.gif" alt="" height="50px" width="50px" />
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
        {weatherData && (
          <div className="weather-card row-layout">
            <div className="weather-info">
              <div>
                <div className="location-temp">
                  <div className="location">
                    <h2>{weatherData.weather?.city || weatherData.location?.city}</h2>
                    {weatherData.location && (
                      <p>📍{weatherData.location.lat.toFixed(4)}, {weatherData.location.lon.toFixed(4)}</p>
                    )}
                  </div>
                  <div className="temperature">
                    <span className="icon">{getWeatherIcon(weatherData.weather.description)}</span>
                    <span className="temp">{weatherData.weather.temperature}°C</span>
                    <div className="weather-description">
                      {weatherData.weather.description || 'Weather'}
                    </div>
                  </div>
                </div>
                <div className="details">
                  <div className="detail">
                    <span className="label">Humidity</span>
                    <span className="value">💧 {weatherData.weather.humidity}%</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="ai-suggestions">
              <h3><span id='ai'>✦︎</span> Suggestions</h3>
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
          </div>
        )}
        <footer>
          <button onClick={() => fetchWeather()} className="refresh-btn">
          ⟳ Refresh Current Location
          </button>
        </footer>
      </div>
    </div>
  )
}

export default App
