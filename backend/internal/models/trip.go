package models

import "time"

// Trip mirrors models/trip.py's PhysicalTrip — deliberately NOT including
// gps_points here, since that field can be large and this struct backs a
// list view (many trips per page), not a single-trip detail view. Add a
// separate TripDetail struct later if a map view needs the full GPS trace.
type Trip struct {
	TripID        string    `bson:"trip_id" json:"tripId"`
	Unit          string    `bson:"unit" json:"unit"`
	FleetID       string    `bson:"fleet_id" json:"fleetId"`
	StartTime     time.Time `bson:"start_time" json:"startTime"`
	EndTime       time.Time `bson:"end_time" json:"endTime"`
	RouteIDs      []string  `bson:"route_ids" json:"routeIds"`
	GPSPointCount int       `bson:"gps_point_count" json:"gpsPointCount"`

	// Populated by the repository's $lookup join against `mismatches`, not
	// stored on the trip document itself — a trip has no inherent opinion
	// about its own mismatches, that's reconciliation's job.
	MismatchCount int      `bson:"mismatchCount" json:"mismatchCount"`
	MismatchTypes []string `bson:"mismatchTypes" json:"mismatchTypes"`
}
