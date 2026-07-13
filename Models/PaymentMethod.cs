namespace Parkify.API.Models;

public class PaymentMethod
{
    public Guid Id { get; set; }
    public Guid UserId { get; set; }
    public string MethodType { get; set; } = "card";
    public string? LastFour { get; set; }
    public string? CardHolder { get; set; }
    public string? Expiry { get; set; }
    public bool IsDefault { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public User User { get; set; } = null!;
}
