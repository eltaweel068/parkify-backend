namespace Parkify.API.Models;

public class Car
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string LicensePlate { get; set; } = string.Empty;
    public string? Make { get; set; }
    public string? Model { get; set; }
    public int? Year { get; set; }
    public string? Color { get; set; }
    public bool IsDefault { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public User User { get; set; } = null!;
}
