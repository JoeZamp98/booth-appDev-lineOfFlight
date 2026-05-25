from constants import AIRPORTS, SPC_URLS, SPC_RISK_LEVELS
import requests
import logging
from shapely.geometry import Point, shape

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
log = logging.getLogger(__name__)

class StormPredictionCenterFetcher:

    def __init__(self):
        """
        Args:
            None
        """
    def get_spc_risk_level(
        self,
        airport: str,
        day: int
    ) -> int:
        """
        Get SPC convective risk level for an airport.

        Args:
            airport: IATA code
            day:     Outlook day (1, 2, or 3)

        Returns:
            Integer 0-6 (0 = no risk, 6 = HIGH)
        """

        if airport not in AIRPORTS:

            raise ValueError(f"Unknown airport: '{airport}'.  Added information for this airport in the AIRPORTS dictionary.")

        try: 

            resp = requests.get(SPC_URLS[day])

            log.info(f"Fetch SPC outlook for {airport} on day {day}: {resp.json()}")

        except Exception as e: 

            log.warning(f"Error fetching SPC outlook for {airport} on day {day}: {e}")

            return 0

        geojson = resp
        info = AIRPORTS[airport]
        airport_point = Point(info['lon'], info['lat'])

        risk = self._determine_risk_level(geojson, airport_point)

        return risk

    
    def get_spc_risk_all_airports(
        self,
        day: int
    ) -> dict[str, int]:
        """Returns SPC risk level for all airports in the AIRPORTS dict."""

        return {code: self.get_spc_risk_level(code, day) for code in AIRPORTS.keys()}

    def _determine_risk_level(
        self,
        outlook,
        point
    ) -> int:

        highest_risk = 0

        for feature in outlook.get("features", []):

            try:
                label = feature["properties"].get("label", "")
                risk_level = SPC_RISK_LEVELS.get(label, 0)

                if risk_level > 0:
                    polygon = shape(feature["geometry"])

                    if polygon.contains(point):
                        highest_risk = max(highest_risk, risk_level)

            except Exception as e: 
                
                continue

        return highest_risk



if __name__ == "__main__":

    fetcher = StormPredictionCenterFetcher()

    fetcher.get_spc_risk_all_airports(1)

