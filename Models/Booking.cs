namespace Parkify.API.Models;

public class Booking
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public Guid ParkingId { get; set; }
    public Guid SlotId { get; set; }
    public string VehiclePlate { get; set; } = string.Empty;
    public DateTime StartTime { get; set; }
    public DateTime EndTime { get; set; }
    public DateTime? ActualExitTime { get; set; }
    public string Status { get; set; } = "confirmed";
    public double TotalHours { get; set; }
    public double Amount { get; set; }
    public double Fees { get; set; }
    public double TotalAmount { get; set; }
    public string Currency { get; set; } = "EGP";
    public string PaymentStatus { get; set; } = "pending";
    public string PaymentMethod { get; set; } = "card";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public User User { get; set; } = null!;
    public Parking Parking { get; set; } = null!;
    public ParkingSlot Slot { get; set; } = null!;
}
