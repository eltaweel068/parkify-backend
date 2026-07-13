namespace Parkify.API.DTOs;

public class AlertResponse
{
    public Guid Id { get; init; }
    public Guid ParkingId { get; init; }
    public string ParkingName { get; init; } = string.Empty;
    public string AlertType { get; init; } = string.Empty;
    public string Severity { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
    public string Status { get; init; } = "active";
    public string CreatedAt { get; init; } = string.Empty;
    public string? ResolvedAt { get; init; }
    public string? ResolvedBy { get; init; }
}

public class VehicleLogResponse
{
    public Guid Id { get; init; }
    public Guid ParkingId { get; init; }
    public string ParkingName { get; init; } = string.Empty;
    public string VehiclePlate { get; init; } = string.Empty;
    public string Action { get; init; } = string.Empty;
    public string Gate { get; init; } = string.Empty;
    public string Timestamp { get; init; } = string.Empty;
    public string? PlateImage { get; init; }
    public double? Confidence { get; init; }
}
