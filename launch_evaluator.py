import time
import requests
from typing import Dict, Any, List

API_KEY = "011b7a566766f3276916771e2e23c64c"

class LaunchConditionAnalyzer:
    def __init__(self, api_key: str = API_KEY):
        self.api_key = api_key
        self.cache: Dict[str, Dict[str, Any]] = {}

    def fetch_weather_for_coords(self, lat: float, lon: float) -> Dict[str, Any]:
        """Queries WeatherAPI once per coordinate pair and locks/caches it."""
        cache_key = f"{round(lat, 2)},{round(lon, 2)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        url = f"https://api.weatherapi.com/v1/current.json?key={self.api_key}&q={cache_key}&aqi=no"
        try:
            res = requests.get(url, timeout=3.5).json()
            curr = res.get("current", {})
            loc = res.get("location", {})
            loc_label = f"{loc.get('name', 'Launch Site')}, {loc.get('country', '')}".strip(", ")

            data = {
                "location_name": loc_label or f"Coords [{lat:.2f}, {lon:.2f}]",
                "lat": float(lat),
                "lon": float(lon),
                "wind_speed": round(curr.get("wind_kph", 14.4) / 3.6, 2),
                "wind_gust": round(curr.get("gust_kph", 18.0) / 3.6, 2),
                "wind_direction": float(curr.get("wind_degree", 120.0)),
                "temperature": float(curr.get("temp_c", 25.0)),
                "pressure": float(curr.get("pressure_mb", 1013.2)),
                "humidity": float(curr.get("humidity", 50.0)),
                "precipitation_rate": float(curr.get("precip_mm", 0.0)),
                "source": f"WeatherAPI Live ({loc_label})"
            }
        except Exception:
            data = {
                "location_name": f"Launch Site [{lat:.2f}, {lon:.2f}]",
                "lat": float(lat),
                "lon": float(lon),
                "wind_speed": 4.5,
                "wind_gust": 6.2,
                "wind_direction": 135.0,
                "temperature": 26.0,
                "pressure": 1012.0,
                "humidity": 50.0,
                "precipitation_rate": 0.0,
                "source": "Offline Fallback"
            }

        self.cache[cache_key] = data
        return data

    def calculate_density_altitude(self, temp_c: float, pressure_hpa: float, humidity: float) -> float:
        """USP: Calculates Density Altitude (meters) - affects rocket drag and motor output."""
        standard_pressure = 1013.25
        pressure_alt = (1.0 - (pressure_hpa / standard_pressure)**0.190288) * 44330.8
        isa_temp = 15.0 - (6.5 * (pressure_alt / 1000.0))
        temp_dev = temp_c - isa_temp
        density_alt = pressure_alt + (118.8 * temp_dev)
        return round(density_alt, 1)

    def calculate_risk_index(self, w: dict) -> int:
        """USP: Calculates a 0% to 100% composite Launch Risk Index based on weather stress."""
        score = 0
        # Wind contribution (Max limit 11 m/s -> up to 40%)
        score += min(40, int((w["wind_speed"] / 11.0) * 40))
        # Gust contribution (Max limit 13 m/s -> up to 30%)
        score += min(30, int((w["wind_gust"] / 13.0) * 30))
        # Rain contribution -> up to 30%
        if w["precipitation_rate"] > 0:
            score += min(30, int(w["precipitation_rate"] * 15))
        return min(100, score)

    def evaluate_flight_readiness(self, weather: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates conditions against Launch Commit Criteria and injects USPs."""
        red_reasons = []
        yellow_reasons = []

        ws = weather["wind_speed"]
        if ws > 11.0:
            red_reasons.append(f"Surface wind {ws} m/s exceeds max abort limit (11.0 m/s)")
        elif ws > 8.0:
            yellow_reasons.append(f"Elevated surface wind {ws} m/s (Threshold: 8.0 m/s)")

        wg = weather["wind_gust"]
        if wg > 13.0:
            red_reasons.append(f"Hazardous gusts {wg} m/s (Abort limit: 13.0 m/s)")
        elif wg > 10.0:
            yellow_reasons.append(f"Moderate gusts {wg} m/s")

        precip = weather["precipitation_rate"]
        if precip > 1.0:
            red_reasons.append(f"Active rainfall {precip} mm/h (avionics hazard)")
        elif precip > 0.0:
            yellow_reasons.append(f"Trace precipitation {precip} mm/h detected")

        t = weather["temperature"]
        if t < -5.0 or t > 42.0:
            red_reasons.append(f"Motor grain thermal limit breached: {t} °C")
        elif t < 0.0 or t > 38.0:
            yellow_reasons.append(f"Sub-optimal thermal range: {t} °C")

        if red_reasons:
            status, badge, reasons = "UNSUITABLE", "red", red_reasons + yellow_reasons
        elif yellow_reasons:
            status, badge, reasons = "CAUTION", "yellow", yellow_reasons
        else:
            status, badge, reasons = "ACCEPTABLE", "green", ["All environmental parameters nominal for flight."]

        # Calculate USPs
        risk_score = self.calculate_risk_index(weather)
        density_alt = self.calculate_density_altitude(
            weather["temperature"], 
            weather["pressure"], 
            weather["humidity"]
        )

        return {
            "status": status,
            "badge_color": badge,
            "reasons": reasons,
            "weather": weather,
            "usp_risk_index": risk_score,
            "usp_density_altitude": density_alt
        }

    def generate_storm_stages(self, baseline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generates Green -> Yellow -> Red storm progression relative to current site weather."""
        return [
            {
                "phase_name": f"T-30m: Nominal Baseline at {baseline['location_name']}",
                "location_name": baseline["location_name"],
                "wind_speed": baseline["wind_speed"],
                "wind_gust": baseline["wind_gust"],
                "wind_direction": baseline["wind_direction"],
                "temperature": baseline["temperature"],
                "pressure": baseline["pressure"],
                "humidity": baseline["humidity"],
                "precipitation_rate": 0.0,
                "source": baseline["source"]
            },
            {
                "phase_name": "T-15m: Gust Front Detected (Caution Zone)",
                "location_name": baseline["location_name"],
                "wind_speed": round(baseline["wind_speed"] + 4.5, 2),
                "wind_gust": round(baseline["wind_gust"] + 5.2, 2),
                "wind_direction": (baseline["wind_direction"] + 35) % 360,
                "temperature": baseline["temperature"] - 2.5,
                "pressure": baseline["pressure"] - 4.5,
                "humidity": min(100.0, baseline["humidity"] + 20.0),
                "precipitation_rate": 0.4,
                "source": "Simulated Weather Transition"
            },
            {
                "phase_name": "T-0m: Squall Line Over Launch Pad (Flight Abort)",
                "location_name": baseline["location_name"],
                "wind_speed": round(baseline["wind_speed"] + 9.5, 2),
                "wind_gust": round(baseline["wind_gust"] + 11.0, 2),
                "wind_direction": (baseline["wind_direction"] + 75) % 360,
                "temperature": baseline["temperature"] - 6.0,
                "pressure": baseline["pressure"] - 12.0,
                "humidity": 95.0,
                "precipitation_rate": 5.8,
                "source": "Simulated Weather Transition"
            }
        ]