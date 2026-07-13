namespace Parkify.API.Models;

public class Alert
{
    public Guid Id { get; set; }
    public Guid ParkingId { get; set; }
    public string AlertType { get; set; } = string.Empty;
    public string Severity { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string Status { get; set; } = "active";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? ResolvedAt { get; set; }
    public Guid? ResolvedBy { get; set; }

    public Parking Parking { get; set; } = null!;
}
