namespace Parkify.API.Models;

public class ParkingSlot
{
    public Guid Id { get; set; }
    public Guid ParkingId { get; set; }
    public string SlotNumber { get; set; } = string.Empty;
    public int Floor { get; set; } = 1;
    public string? Section { get; set; }
    public string Status { get; set; } = "available";
    public bool IsHandicap { get; set; }
    public bool IsEvCharging { get; set; }
    public string? CurrentVehiclePlate { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Parking Parking { get; set; } = null!;
}
