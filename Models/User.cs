namespace Parkify.API.Models;

public class User
{
    public Guid Id { get; set; }
    public string Email { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? Phone { get; set; }
    public string? PasswordHash { get; set; }
    public string Role { get; set; } = "user";
    public bool IsActive { get; set; } = true;
    public string? Gender { get; set; }
    public string? Address { get; set; }
    public string? ProfilePhoto { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public ICollection<Car> Cars { get; set; } = new List<Car>();
    public ICollection<PaymentMethod> PaymentMethods { get; set; } = new List<PaymentMethod>();
    public ICollection<Favorite> Favorites { get; set; } = new List<Favorite>();
    public ICollection<Notification> Notifications { get; set; } = new List<Notification>();
    public ICollection<Booking> Bookings { get; set; } = new List<Booking>();
    public ICollection<SpotWatcher> SpotWatchers { get; set; } = new List<SpotWatcher>();
    public ICollection<SupportTicket> SupportTickets { get; set; } = new List<SupportTicket>();
}
