DUMMY_PREDICTIONS = {
    "DL-1221": {
        "flight":       "DL 1221",
        "carrier":      "DL",
        "origin":       "SFO",
        "dest":         "JFK",
        "dep_time":     "17:10",
        "arr_time":     "01:42",
        "arr_plus_day": True,
        "aircraft":     "Airbus A330-900neo",
        "seat":         "2A",
        "status":       "On time",
        "delay_prob":   0.45,
        "likely_delay": 42,
        "drivers": [
            {
                "label":    "JFK arrival flow",
                "delta":    "+38%",
                "severity": "high",
                "detail":   "ZNY restricting east arrivals through 22:00 EDT."
            },
            {
                "label":    "SFO marine layer",
                "delta":    "+22%",
                "severity": "medium",
                "detail":   "200ft ceiling expected 19:30 PDT."
            },
            {
                "label":    "Historical pattern",
                "delta":    "+4%",
                "severity": "positive",
                "detail":   "DL 1221 on-time 71% of last 30 evenings."
            },
        ],
    }
}
