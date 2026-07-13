namespace Parkify.API.DTOs;

public class NotificationResponse
{
    public Guid Id { get; init; }
    public Guid UserId { get; init; }
    public string Title { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
    public string NotificationType { get; init; } = string.Empty;
    public bool IsRead { get; init; }
    public object? Data { get; init; }
    public string CreatedAt { get; init; } = string.Empty;
}

public record UnreadCountResponse(int Count);
