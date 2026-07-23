"""The mock resource tree — single source of truth for Phase 1 in-memory
repositories and (Phase 2) Postgres seeding. Do not redefine this data
elsewhere.

Same geography theme as the original flat Map/Layer catalog, reorganized into
the 5-level hierarchy: Workspace -> Folder(nestable) -> Map -> Group/Layer."""

from __future__ import annotations

from permissions_server.domain.entities import Resource, ResourceType, Team

RESOURCES: list[Resource] = [
    Resource(id="ws-city", type=ResourceType.WORKSPACE, name="City Planning", parent_id=None),
    # --- Infrastructure ---
    Resource(id="f-infrastructure", type=ResourceType.FOLDER, name="Infrastructure", parent_id="ws-city"),
    Resource(id="map-city-roads", type=ResourceType.MAP, name="City Roads", parent_id="f-infrastructure"),
    Resource(id="layer-roads-highways", type=ResourceType.LAYER, name="Highways", parent_id="map-city-roads"),
    Resource(id="layer-roads-local", type=ResourceType.LAYER, name="Local Streets", parent_id="map-city-roads"),
    Resource(id="layer-roads-bike", type=ResourceType.LAYER, name="Bike Lanes", parent_id="map-city-roads"),
    Resource(id="map-utilities", type=ResourceType.MAP, name="Utility Lines", parent_id="f-infrastructure"),
    Resource(id="group-utilities-underground", type=ResourceType.GROUP, name="Underground", parent_id="map-utilities"),
    Resource(id="layer-util-water", type=ResourceType.LAYER, name="Water Mains", parent_id="group-utilities-underground"),
    Resource(id="layer-util-sewer", type=ResourceType.LAYER, name="Sewer Lines", parent_id="group-utilities-underground"),
    Resource(id="layer-util-power", type=ResourceType.LAYER, name="Power Grid", parent_id="map-utilities"),
    Resource(id="map-transit", type=ResourceType.MAP, name="Public Transit Routes", parent_id="f-infrastructure"),
    Resource(id="layer-transit-bus", type=ResourceType.LAYER, name="Bus Routes", parent_id="map-transit"),
    Resource(id="layer-transit-rail", type=ResourceType.LAYER, name="Rail Lines", parent_id="map-transit"),
    Resource(id="layer-transit-stops", type=ResourceType.LAYER, name="Stops & Stations", parent_id="map-transit"),
    # --- Land Use ---
    Resource(id="f-land-use", type=ResourceType.FOLDER, name="Land Use", parent_id="ws-city"),
    Resource(id="map-zoning", type=ResourceType.MAP, name="Zoning Districts", parent_id="f-land-use"),
    Resource(id="layer-zoning-residential", type=ResourceType.LAYER, name="Residential", parent_id="map-zoning"),
    Resource(id="layer-zoning-commercial", type=ResourceType.LAYER, name="Commercial", parent_id="map-zoning"),
    Resource(id="layer-zoning-industrial", type=ResourceType.LAYER, name="Industrial", parent_id="map-zoning"),
    Resource(id="map-parcels", type=ResourceType.MAP, name="Property Parcels", parent_id="f-land-use"),
    Resource(id="layer-parcels-boundaries", type=ResourceType.LAYER, name="Parcel Boundaries", parent_id="map-parcels"),
    Resource(id="layer-parcels-assessed", type=ResourceType.LAYER, name="Assessed Values", parent_id="map-parcels"),
    Resource(id="map-schools", type=ResourceType.MAP, name="School Districts", parent_id="f-land-use"),
    Resource(id="layer-schools-elementary", type=ResourceType.LAYER, name="Elementary", parent_id="map-schools"),
    Resource(id="layer-schools-secondary", type=ResourceType.LAYER, name="Secondary", parent_id="map-schools"),
    # --- Environment (with a nested Folder, demonstrating Folder-in-Folder) ---
    Resource(id="f-environment", type=ResourceType.FOLDER, name="Environment", parent_id="ws-city"),
    Resource(id="f-hazards", type=ResourceType.FOLDER, name="Hazards", parent_id="f-environment"),
    Resource(id="map-flood-zones", type=ResourceType.MAP, name="Flood Risk Zones", parent_id="f-hazards"),
    Resource(id="layer-flood-100yr", type=ResourceType.LAYER, name="100-Year Floodplain", parent_id="map-flood-zones"),
    Resource(id="layer-flood-500yr", type=ResourceType.LAYER, name="500-Year Floodplain", parent_id="map-flood-zones"),
    Resource(id="map-wildfire", type=ResourceType.MAP, name="Wildfire Hazard Areas", parent_id="f-hazards"),
    Resource(id="layer-wildfire-high", type=ResourceType.LAYER, name="High Hazard", parent_id="map-wildfire"),
    Resource(id="layer-wildfire-moderate", type=ResourceType.LAYER, name="Moderate Hazard", parent_id="map-wildfire"),
    Resource(id="map-water", type=ResourceType.MAP, name="Water Resources", parent_id="f-environment"),
    Resource(id="layer-water-rivers", type=ResourceType.LAYER, name="Rivers & Streams", parent_id="map-water"),
    Resource(id="layer-water-reservoirs", type=ResourceType.LAYER, name="Reservoirs", parent_id="map-water"),
    Resource(id="layer-water-wells", type=ResourceType.LAYER, name="Wells", parent_id="map-water"),
    Resource(id="map-parks", type=ResourceType.MAP, name="Parks & Recreation", parent_id="f-environment"),
    Resource(id="layer-parks-trails", type=ResourceType.LAYER, name="Trails", parent_id="map-parks"),
    Resource(id="layer-parks-facilities", type=ResourceType.LAYER, name="Facilities", parent_id="map-parks"),
]

TEAMS: list[Team] = [
    Team(id="team-north-ops", name="North Region Ops"),
    Team(id="team-gis-analysts", name="GIS Analysts"),
]

TEAM_MEMBERSHIPS: dict[str, list[str]] = {
    "team-north-ops": ["u016", "u017"],
    "team-gis-analysts": ["u020", "u021", "u022"],
}
