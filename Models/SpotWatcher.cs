namespace Parkify.API.Models;

public class SpotWatcher
{
    public Guid Id { get; set; }
    public Guid ParkingId { get; set; }
    public Guid UserId { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public Parking Parking { get; set; } = null!;
    public User User { get; set; } = null!;
}
