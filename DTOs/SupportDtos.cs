namespace Parkify.API.DTOs;

public record SupportTicketCreateRequest(
    string Subject,
    string Message,
    string Category = "general"
);

public class SupportTicketResponse
{
    public Guid Id { get; init; }
    public Guid UserId { get; init; }
    public string Subject { get; init; } = string.Empty;
    public string Message { get; init; } = string.Empty;
    public string Category { get; init; } = string.Empty;
    public string Status { get; init; } = "open";
    public string CreatedAt { get; init; } = string.Empty;
    public string? UpdatedAt { get; init; }
}
