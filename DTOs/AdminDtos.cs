namespace Parkify.API.DTOs;

public class DashboardStats
{
    public int TotalParkings { get; init; }
    public int TotalSlots { get; init; }
    public int AvailableSlots { get; init; }
    public int OccupiedSlots { get; init; }
    public int TotalUsers { get; init; }
    public int ActiveBookings { get; init; }
    public int TodayBookings { get; init; }
    public double TodayRevenue { get; init; }
    public int PendingAlerts { get; init; }
    public string Currency { get; init; } = "EGP";
}

public record GateControlRequest(string GateType = "entry", string Action = "open", string? Reason = null);

public record AdminSendNotificationRequest(
    Guid? UserId,
    string Title,
    string Message,
    string NotificationType = "system"
);

public record UserStatusUpdateRequest(bool IsActive, string? Reason = null);

public class FavoriteResponse
{
    public Guid Id { get; init; }
    public Guid UserId { get; init; }
    public Guid ParkingId { get; init; }
    public ParkingResponse Parking { get; init; } = new();
    public string CreatedAt { get; init; } = string.Empty;
}
