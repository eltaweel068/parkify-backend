namespace Parkify.API.DTOs;

public record BookingCreateRequest(
    Guid ParkingId,
    Guid SlotId,
    string VehiclePlate,
    DateTime StartTime,
    double DurationHours,
    string PaymentMethod = "card"
);

public class BookingResponse
{
    public Guid Id { get; init; }
    public Guid UserId { get; init; }
    public Guid ParkingId { get; init; }
    public string ParkingName { get; init; } = string.Empty;
    public string ParkingAddress { get; init; } = string.Empty;
    public Guid SlotId { get; init; }
    public string SlotNumber { get; init; } = string.Empty;
    public int Floor { get; init; }
    public string? Section { get; init; }
    public string VehiclePlate { get; init; } = string.Empty;
    public DateTime StartTime { get; init; }
    public DateTime EndTime { get; init; }
    public DateTime? ActualExitTime { get; init; }
    public string Status { get; init; } = string.Empty;
    public double TotalHours { get; init; }
    public double Amount { get; init; }
    public double Fees { get; init; }
    public double TotalAmount { get; init; }
    public string Currency { get; init; } = "EGP";
    public string PaymentStatus { get; init; } = string.Empty;
    public string PaymentMethod { get; init; } = string.Empty;
    public DateTime CreatedAt { get; init; }
}

public class ActiveBookingResponse
{
    public Guid Id { get; init; }
    public string ParkingName { get; init; } = string.Empty;
    public string ParkingAddress { get; init; } = string.Empty;
    public Guid SlotId { get; init; }
    public string SlotNumber { get; init; } = string.Empty;
    public int Floor { get; init; }
    public int RemainingTimeSeconds { get; init; }
    public DateTime StartTime { get; init; }
    public DateTime EndTime { get; init; }
}

public class BookingQRResponse
{
    public Guid BookingId { get; init; }
    public string QrData { get; init; } = string.Empty;
    public string ParkingName { get; init; } = string.Empty;
    public string SlotNumber { get; init; } = string.Empty;
    public string StartTime { get; init; } = string.Empty;
    public string EndTime { get; init; } = string.Empty;
    public string VehiclePlate { get; init; } = string.Empty;
}

public record BookingExtendRequest(double AdditionalHours);
