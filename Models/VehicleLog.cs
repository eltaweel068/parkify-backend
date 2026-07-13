namespace Parkify.API.Models;

public class VehicleLog
{
    public Guid Id { get; set; }
    public Guid ParkingId { get; set; }
    public string VehiclePlate { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string? Gate { get; set; }
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string? PlateImage { get; set; }
    public double? Confidence { get; set; }

    public Parking Parking { get; set; } = null!;
}
