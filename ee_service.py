"""Earth Engine REST API service for creating map tiles and fetching data."""

import requests

import config
import ee_auth

# ---------------------------------------------------------------------------
# Predefined data layers with their EE expression graphs and visualization
# ---------------------------------------------------------------------------

DATA_LAYERS = {
    "elevation": {
        "name": "SRTM Elevation",
        "description": "Shuttle Radar Topography Mission 30m digital elevation model",
        "dataset": "USGS/SRTMGL1_003",
        "expression": {
            "result": "0",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "Image.load",
                        "arguments": {
                            "id": {"constantValue": "USGS/SRTMGL1_003"}
                        },
                    }
                }
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["elevation"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 6000}],
            "paletteColors": [
                "006633",
                "E5FFCC",
                "662A00",
                "D8D8D8",
                "F5F5F5",
            ],
        },
    },
    "land_cover": {
        "name": "ESA WorldCover 2021",
        "description": "ESA WorldCover 10m land cover classification",
        "dataset": "ESA/WorldCover/v200",
        "expression": {
            "result": "1",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "ImageCollection.load",
                        "arguments": {
                            "id": {"constantValue": "ESA/WorldCover/v200"}
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Collection.first",
                        "arguments": {"collection": {"valueReference": "0"}},
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["Map"],
        "visualizationOptions": {
            "ranges": [{"min": 10, "max": 100}],
            "paletteColors": [
                "006400",
                "FFBB22",
                "FFFF4C",
                "F096FF",
                "FA0000",
                "B4B4B4",
                "F0F0F0",
                "0064C8",
                "0096A0",
                "00CF75",
                "FAE6A0",
            ],
        },
    },
    "temperature": {
        "name": "Land Surface Temperature",
        "description": "MODIS 8-day land surface temperature",
        "dataset": "MODIS/061/MOD11A2",
        "expression": {
            "result": "2",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "ImageCollection.load",
                        "arguments": {
                            "id": {"constantValue": "MODIS/061/MOD11A2"}
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Collection.first",
                        "arguments": {"collection": {"valueReference": "0"}},
                    }
                },
                "2": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "1"},
                            "bandSelectors": {
                                "constantValue": ["LST_Day_1km"]
                            },
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["LST_Day_1km"],
        "visualizationOptions": {
            "ranges": [{"min": 13000, "max": 16500}],
            "paletteColors": [
                "040274",
                "040281",
                "0502a3",
                "0502b8",
                "0502ce",
                "0502e6",
                "0602ff",
                "235cb1",
                "307ef3",
                "269db1",
                "30c8e2",
                "32d3ef",
                "3be285",
                "3ff38f",
                "86e26f",
                "3ae237",
                "b5e22e",
                "d6e21f",
                "fff705",
                "ffd611",
                "ffb613",
                "ff8b13",
                "ff6e08",
                "ff500d",
                "ff0000",
                "de0101",
                "c21301",
                "a71001",
                "911003",
            ],
        },
    },
    "ndvi": {
        "name": "NDVI Vegetation Index",
        "description": "MODIS 16-day Normalized Difference Vegetation Index",
        "dataset": "MODIS/061/MOD13A2",
        "expression": {
            "result": "2",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "ImageCollection.load",
                        "arguments": {
                            "id": {"constantValue": "MODIS/061/MOD13A2"}
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Collection.first",
                        "arguments": {"collection": {"valueReference": "0"}},
                    }
                },
                "2": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "1"},
                            "bandSelectors": {"constantValue": ["NDVI"]},
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["NDVI"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 9000}],
            "paletteColors": [
                "ffffff",
                "ce7e45",
                "df923d",
                "f1b555",
                "fcd163",
                "99b718",
                "74a901",
                "66a000",
                "529400",
                "3e8601",
                "207401",
                "056201",
                "004c00",
                "023b01",
                "012e01",
                "011d01",
                "011301",
            ],
        },
    },
    "nightlights": {
        "name": "Night Lights",
        "description": "VIIRS Stray Light Corrected Nighttime Day/Night Band",
        "dataset": "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
        "expression": {
            "result": "2",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "ImageCollection.load",
                        "arguments": {
                            "id": {
                                "constantValue": "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
                            }
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Collection.first",
                        "arguments": {"collection": {"valueReference": "0"}},
                    }
                },
                "2": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "1"},
                            "bandSelectors": {
                                "constantValue": ["avg_rad"]
                            },
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["avg_rad"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 60}],
            "paletteColors": ["000000", "FFFF00", "FFA500", "FF0000", "FFFFFF"],
        },
    },
    "population": {
        "name": "Population Density",
        "description": "WorldPop Global Project population count per grid cell",
        "dataset": "WorldPop/GP/100m/pop",
        "expression": {
            "result": "2",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "ImageCollection.load",
                        "arguments": {
                            "id": {
                                "constantValue": "WorldPop/GP/100m/pop"
                            }
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Collection.first",
                        "arguments": {"collection": {"valueReference": "0"}},
                    }
                },
                "2": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "1"},
                            "bandSelectors": {
                                "constantValue": ["population"]
                            },
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["population"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 1000}],
            "paletteColors": [
                "FFFFCC",
                "A1DAB4",
                "41B6C4",
                "2C7FB8",
                "253494",
            ],
        },
    },
    "water": {
        "name": "Surface Water",
        "description": "JRC Global Surface Water occurrence",
        "dataset": "JRC/GSW1_4/GlobalSurfaceWater",
        "expression": {
            "result": "1",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "Image.load",
                        "arguments": {
                            "id": {
                                "constantValue": "JRC/GSW1_4/GlobalSurfaceWater"
                            }
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "0"},
                            "bandSelectors": {
                                "constantValue": ["occurrence"]
                            },
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["occurrence"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 100}],
            "paletteColors": ["FFFFFF", "D8D8FF", "4444FF", "0000AA"],
        },
    },
    "tree_cover": {
        "name": "Tree Cover",
        "description": "Hansen Global Forest Change tree cover percentage in year 2000",
        "dataset": "UMD/hansen/global_forest_change_2023_v1_11",
        "expression": {
            "result": "1",
            "values": {
                "0": {
                    "functionInvocationValue": {
                        "functionName": "Image.load",
                        "arguments": {
                            "id": {
                                "constantValue": "UMD/hansen/global_forest_change_2023_v1_11"
                            }
                        },
                    }
                },
                "1": {
                    "functionInvocationValue": {
                        "functionName": "Image.select",
                        "arguments": {
                            "input": {"valueReference": "0"},
                            "bandSelectors": {
                                "constantValue": ["treecover2000"]
                            },
                        },
                    }
                },
            },
        },
        "fileFormat": "PNG_TILES",
        "bandIds": ["treecover2000"],
        "visualizationOptions": {
            "ranges": [{"min": 0, "max": 100}],
            "paletteColors": ["FFFFCC", "D9F0A3", "ADDD8E", "78C679", "31A354", "006837"],
        },
    },
}


def _project_path() -> str:
    return f"projects/{config.GOOGLE_CLOUD_PROJECT}"


def create_map(layer_id: str) -> dict:
    """Call Earth Engine maps.create and return the EarthEngineMap resource.

    Returns dict with 'name' field containing the map ID needed for tiles.
    """
    layer = DATA_LAYERS.get(layer_id)
    if not layer:
        raise ValueError(f"Unknown layer: {layer_id}")

    url = f"{config.EE_API_BASE}/v1/{_project_path()}/map:export"

    body = {
        "expression": layer["expression"],
        "fileFormat": layer["fileFormat"],
        "bandIds": layer["bandIds"],
        "visualizationOptions": layer["visualizationOptions"],
    }

    resp = requests.post(url, json=body, headers=ee_auth.auth_headers())
    resp.raise_for_status()
    return resp.json()


def get_tile_url(map_name: str, z: int, x: int, y: int) -> str:
    """Construct a tile URL from a map resource name."""
    return (
        f"{config.EE_API_BASE}/v1/"
        f"{map_name}/tiles/{z}/{x}/{y}"
    )


def fetch_tile(map_name: str, z: int, x: int, y: int) -> bytes:
    """Fetch a single map tile as raw PNG bytes."""
    url = get_tile_url(map_name, z, x, y)
    resp = requests.get(url, headers=ee_auth.auth_headers())
    resp.raise_for_status()
    return resp.content


def list_layers() -> list[dict]:
    """Return metadata about all available layers."""
    result = []
    for layer_id, layer in DATA_LAYERS.items():
        result.append(
            {
                "id": layer_id,
                "name": layer["name"],
                "description": layer["description"],
                "dataset": layer["dataset"],
            }
        )
    return result


def get_asset_info(asset_id: str) -> dict:
    """Fetch metadata about an Earth Engine asset."""
    url = f"{config.EE_API_BASE}/v1/{_project_path()}/assets/{asset_id}"
    resp = requests.get(url, headers=ee_auth.auth_headers())
    resp.raise_for_status()
    return resp.json()


def compute_value(expression: dict) -> dict:
    """Evaluate an Earth Engine expression and return the computed value."""
    url = f"{config.EE_API_BASE}/v1/{_project_path()}/value:compute"
    body = {"expression": expression}
    resp = requests.post(url, json=body, headers=ee_auth.auth_headers())
    resp.raise_for_status()
    return resp.json()
