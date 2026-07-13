namespace Parkify.API.Models;

public class Parking
{
    public Guid Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public double Latitude { get; set; }
    public double Longitude { get; set; }
    public string Address { get; set; } = string.Empty;
    public string? City { get; set; }
    public string Country { get; set; } = "Egypt";
    public string ParkingType { get; set; } = "covered";
    public int TotalSlots { get; set; }
    public int AvailableSlots { get; set; }
    public int OccupiedSlots { get; set; }
    public bool IsFull { get; set; }
    public double RatePerHour { get; set; }
    public string Currency { get; set; } = "EGP";
    public List<string> Amenities { get; set; } = new();
    public List<string> Images { get; set; } = new();
    public double Rating { get; set; }
    public int ReviewCount { get; set; }
    public bool Is247 { get; set; } = true;
    public bool IsActive { get; set; } = true;
    public string? DeviceKey { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<ParkingSlot> Slots { get; set; } = new List<ParkingSlot>();
    public ICollection<Booking> Bookings { get; set; } = new List<Booking>();
    public ICollection<Favorite> Favorites { get; set; } = new List<Favorite>();
    public ICollection<Alert> Alerts { get; set; } = new List<Alert>();
    public ICollection<VehicleLog> VehicleLogs { get; set; } = new List<VehicleLog>();
    public ICollection<SpotWatcher> SpotWatchers { get; set; } = new List<SpotWatcher>();
}
