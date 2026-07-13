namespace Parkify.API.DTOs;

public class LocationDto
{
    public double Latitude { get; init; }
    public double Longitude { get; init; }
    public string Address { get; init; } = string.Empty;
    public string? City { get; init; }
    public string? Country { get; init; }
}

public class ParkingResponse
{
    public Guid Id { get; init; }
    public string Name { get; init; } = string.Empty;
    public string? Description { get; init; }
    public LocationDto Location { get; init; } = new();
    public string ParkingType { get; init; } = "covered";
    public int TotalSlots { get; init; }
    public int AvailableSlots { get; init; }
    public int OccupiedSlots { get; init; }
    public bool IsFull { get; init; }
    public double RatePerHour { get; init; }
    public string Currency { get; init; } = "EGP";
    public List<string> Amenities { get; init; } = new();
    public List<string> Images { get; init; } = new();
    public double Rating { get; init; }
    public int ReviewCount { get; init; }
    [System.Text.Json.Serialization.JsonPropertyName("is_24_7")]
    public bool Is247 { get; init; } = true;
    public bool IsActive { get; init; } = true;
    public double? DistanceMeters { get; init; }
    public int? WalkingTimeMinutes { get; init; }
    public bool? IsFavorited { get; init; }
}

public class ParkingSlotResponse
{
    public Guid Id { get; init; }
    public Guid ParkingId { get; init; }
    public string SlotNumber { get; init; } = string.Empty;
    public int Floor { get; init; }
    public string? Section { get; init; }
    public string Status { get; init; } = "available";
    public bool IsHandicap { get; init; }
    public bool IsEvCharging { get; init; }
    public string? CurrentVehiclePlate { get; init; }
}

public record ParkingCreateRequest(
    string Name,
    string? Description,
    double Latitude,
    double Longitude,
    string Address,
    string? City,
    string Country,
    string ParkingType,
    int TotalSlots,
    double RatePerHour,
    string Currency,
    List<string> Amenities,
    bool Is247,
    string? DeviceKey
);

public record ParkingUpdateRequest(
    string? Name,
    string? Description,
    double? Latitude,
    double? Longitude,
    string? Address,
    string? City,
    string? ParkingType,
    double? RatePerHour,
    List<string>? Amenities,
    bool? Is247,
    bool? IsActive,
    string? DeviceKey
);
