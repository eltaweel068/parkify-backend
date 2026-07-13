using Microsoft.EntityFrameworkCore;
using Parkify.API.Models;

namespace Parkify.API.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Car> Cars => Set<Car>();
    public DbSet<PaymentMethod> PaymentMethods => Set<PaymentMethod>();
    public DbSet<Parking> Parkings => Set<Parking>();
    public DbSet<ParkingSlot> ParkingSlots => Set<ParkingSlot>();
    public DbSet<Booking> Bookings => Set<Booking>();
    public DbSet<Favorite> Favorites => Set<Favorite>();
    public DbSet<Notification> Notifications => Set<Notification>();
    public DbSet<Alert> Alerts => Set<Alert>();
    public DbSet<VehicleLog> VehicleLogs => Set<VehicleLog>();
    public DbSet<SupportTicket> SupportTickets => Set<SupportTicket>();
    public DbSet<SpotWatcher> SpotWatchers => Set<SpotWatcher>();
    public DbSet<ResetCode> ResetCodes => Set<ResetCode>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.Entity<User>(e =>
        {
            e.ToTable("users");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.Email).HasColumnName("email").HasMaxLength(255).IsRequired();
            e.Property(x => x.Name).HasColumnName("name").HasMaxLength(255).IsRequired();
            e.Property(x => x.FirstName).HasColumnName("first_name").HasMaxLength(100);
            e.Property(x => x.LastName).HasColumnName("last_name").HasMaxLength(100);
            e.Property(x => x.Phone).HasColumnName("phone").HasMaxLength(50);
            e.Property(x => x.PasswordHash).HasColumnName("password_hash");
            e.Property(x => x.Role).HasColumnName("role").HasMaxLength(20).HasDefaultValue("user");
            e.Property(x => x.IsActive).HasColumnName("is_active").HasDefaultValue(true);
            e.Property(x => x.Gender).HasColumnName("gender").HasMaxLength(20);
            e.Property(x => x.Address).HasColumnName("address");
            e.Property(x => x.ProfilePhoto).HasColumnName("profile_photo");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasIndex(x => x.Email).IsUnique();
        });

        b.Entity<Car>(e =>
        {
            e.ToTable("cars");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.LicensePlate).HasColumnName("license_plate").HasMaxLength(50).IsRequired();
            e.Property(x => x.Make).HasColumnName("make").HasMaxLength(100);
            e.Property(x => x.Model).HasColumnName("model").HasMaxLength(100);
            e.Property(x => x.Year).HasColumnName("year");
            e.Property(x => x.Color).HasColumnName("color").HasMaxLength(50);
            e.Property(x => x.IsDefault).HasColumnName("is_default").HasDefaultValue(false);
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasOne(x => x.User).WithMany(u => u.Cars).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<PaymentMethod>(e =>
        {
            e.ToTable("payment_methods");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.MethodType).HasColumnName("method_type").HasMaxLength(50).IsRequired();
            e.Property(x => x.LastFour).HasColumnName("last_four").HasMaxLength(4);
            e.Property(x => x.CardHolder).HasColumnName("card_holder").HasMaxLength(255);
            e.Property(x => x.Expiry).HasColumnName("expiry").HasMaxLength(10);
            e.Property(x => x.IsDefault).HasColumnName("is_default").HasDefaultValue(false);
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasOne(x => x.User).WithMany(u => u.PaymentMethods).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<Parking>(e =>
        {
            e.ToTable("parkings");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.Name).HasColumnName("name").HasMaxLength(255).IsRequired();
            e.Property(x => x.Description).HasColumnName("description");
            e.Property(x => x.Latitude).HasColumnName("latitude");
            e.Property(x => x.Longitude).HasColumnName("longitude");
            e.Property(x => x.Address).HasColumnName("address").IsRequired();
            e.Property(x => x.City).HasColumnName("city").HasMaxLength(100);
            e.Property(x => x.Country).HasColumnName("country").HasMaxLength(100).HasDefaultValue("Egypt");
            e.Property(x => x.ParkingType).HasColumnName("parking_type").HasMaxLength(50).HasDefaultValue("covered");
            e.Property(x => x.TotalSlots).HasColumnName("total_slots");
            e.Property(x => x.AvailableSlots).HasColumnName("available_slots");
            e.Property(x => x.OccupiedSlots).HasColumnName("occupied_slots").HasDefaultValue(0);
            e.Property(x => x.IsFull).HasColumnName("is_full").HasDefaultValue(false);
            e.Property(x => x.RatePerHour).HasColumnName("rate_per_hour");
            e.Property(x => x.Currency).HasColumnName("currency").HasMaxLength(10).HasDefaultValue("EGP");
            e.Property(x => x.Amenities).HasColumnName("amenities").HasColumnType("text[]");
            e.Property(x => x.Images).HasColumnName("images").HasColumnType("text[]");
            e.Property(x => x.Rating).HasColumnName("rating").HasDefaultValue(0.0);
            e.Property(x => x.ReviewCount).HasColumnName("review_count").HasDefaultValue(0);
            e.Property(x => x.Is247).HasColumnName("is_24_7").HasDefaultValue(true);
            e.Property(x => x.IsActive).HasColumnName("is_active").HasDefaultValue(true);
            e.Property(x => x.DeviceKey).HasColumnName("device_key").HasMaxLength(255);
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
        });

        b.Entity<ParkingSlot>(e =>
        {
            e.ToTable("parking_slots");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.SlotNumber).HasColumnName("slot_number").HasMaxLength(50).IsRequired();
            e.Property(x => x.Floor).HasColumnName("floor").HasDefaultValue(1);
            e.Property(x => x.Section).HasColumnName("section").HasMaxLength(50);
            e.Property(x => x.Status).HasColumnName("status").HasMaxLength(20).HasDefaultValue("available");
            e.Property(x => x.IsHandicap).HasColumnName("is_handicap").HasDefaultValue(false);
            e.Property(x => x.IsEvCharging).HasColumnName("is_ev_charging").HasDefaultValue(false);
            e.Property(x => x.CurrentVehiclePlate).HasColumnName("current_vehicle_plate").HasMaxLength(50);
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasOne(x => x.Parking).WithMany(p => p.Slots).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<Booking>(e =>
        {
            e.ToTable("bookings");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.SlotId).HasColumnName("slot_id");
            e.Property(x => x.VehiclePlate).HasColumnName("vehicle_plate").HasMaxLength(50).IsRequired();
            e.Property(x => x.StartTime).HasColumnName("start_time");
            e.Property(x => x.EndTime).HasColumnName("end_time");
            e.Property(x => x.ActualExitTime).HasColumnName("actual_exit_time");
            e.Property(x => x.Status).HasColumnName("status").HasMaxLength(20).HasDefaultValue("confirmed");
            e.Property(x => x.TotalHours).HasColumnName("total_hours");
            e.Property(x => x.Amount).HasColumnName("amount");
            e.Property(x => x.Fees).HasColumnName("fees").HasDefaultValue(0.0);
            e.Property(x => x.TotalAmount).HasColumnName("total_amount");
            e.Property(x => x.Currency).HasColumnName("currency").HasMaxLength(10).HasDefaultValue("EGP");
            e.Property(x => x.PaymentStatus).HasColumnName("payment_status").HasMaxLength(20).HasDefaultValue("pending");
            e.Property(x => x.PaymentMethod).HasColumnName("payment_method").HasMaxLength(50).HasDefaultValue("card");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasOne(x => x.User).WithMany(u => u.Bookings).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Restrict);
            e.HasOne(x => x.Parking).WithMany(p => p.Bookings).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Restrict);
            e.HasOne(x => x.Slot).WithMany().HasForeignKey(x => x.SlotId).OnDelete(DeleteBehavior.Restrict);
        });

        b.Entity<Favorite>(e =>
        {
            e.ToTable("favorites");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasIndex(x => new { x.UserId, x.ParkingId }).IsUnique();
            e.HasOne(x => x.User).WithMany(u => u.Favorites).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Cascade);
            e.HasOne(x => x.Parking).WithMany(p => p.Favorites).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<Notification>(e =>
        {
            e.ToTable("notifications");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.Title).HasColumnName("title").HasMaxLength(255).IsRequired();
            e.Property(x => x.Message).HasColumnName("message").IsRequired();
            e.Property(x => x.NotificationType).HasColumnName("notification_type").HasMaxLength(50).IsRequired();
            e.Property(x => x.IsRead).HasColumnName("is_read").HasDefaultValue(false);
            e.Property(x => x.Data).HasColumnName("data").HasColumnType("jsonb");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasOne(x => x.User).WithMany(u => u.Notifications).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<Alert>(e =>
        {
            e.ToTable("alerts");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.AlertType).HasColumnName("alert_type").HasMaxLength(50).IsRequired();
            e.Property(x => x.Severity).HasColumnName("severity").HasMaxLength(20).IsRequired();
            e.Property(x => x.Message).HasColumnName("message").IsRequired();
            e.Property(x => x.Status).HasColumnName("status").HasMaxLength(20).HasDefaultValue("active");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.ResolvedAt).HasColumnName("resolved_at");
            e.Property(x => x.ResolvedBy).HasColumnName("resolved_by");
            e.HasOne(x => x.Parking).WithMany(p => p.Alerts).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Restrict);
        });

        b.Entity<VehicleLog>(e =>
        {
            e.ToTable("vehicle_logs");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.VehiclePlate).HasColumnName("vehicle_plate").HasMaxLength(50).IsRequired();
            e.Property(x => x.Action).HasColumnName("action").HasMaxLength(20).IsRequired();
            e.Property(x => x.Gate).HasColumnName("gate").HasMaxLength(100);
            e.Property(x => x.Timestamp).HasColumnName("timestamp");
            e.Property(x => x.PlateImage).HasColumnName("plate_image");
            e.Property(x => x.Confidence).HasColumnName("confidence");
            e.HasOne(x => x.Parking).WithMany(p => p.VehicleLogs).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Restrict);
        });

        b.Entity<SupportTicket>(e =>
        {
            e.ToTable("support_tickets");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.Subject).HasColumnName("subject").HasMaxLength(255).IsRequired();
            e.Property(x => x.Message).HasColumnName("message").IsRequired();
            e.Property(x => x.Category).HasColumnName("category").HasMaxLength(50).HasDefaultValue("general");
            e.Property(x => x.Status).HasColumnName("status").HasMaxLength(20).HasDefaultValue("open");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.UpdatedAt).HasColumnName("updated_at");
            e.HasOne(x => x.User).WithMany(u => u.SupportTickets).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Restrict);
        });

        b.Entity<SpotWatcher>(e =>
        {
            e.ToTable("spot_watchers");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.ParkingId).HasColumnName("parking_id");
            e.Property(x => x.UserId).HasColumnName("user_id");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.HasIndex(x => new { x.ParkingId, x.UserId }).IsUnique();
            e.HasOne(x => x.Parking).WithMany(p => p.SpotWatchers).HasForeignKey(x => x.ParkingId).OnDelete(DeleteBehavior.Cascade);
            e.HasOne(x => x.User).WithMany(u => u.SpotWatchers).HasForeignKey(x => x.UserId).OnDelete(DeleteBehavior.Cascade);
        });

        b.Entity<ResetCode>(e =>
        {
            e.ToTable("reset_codes");
            e.HasKey(x => x.Id);
            e.Property(x => x.Id).HasColumnName("id");
            e.Property(x => x.Email).HasColumnName("email").HasMaxLength(255);
            e.Property(x => x.Phone).HasColumnName("phone").HasMaxLength(50);
            e.Property(x => x.Code).HasColumnName("code").HasMaxLength(10).IsRequired();
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.ExpiresAt).HasColumnName("expires_at");
            e.Property(x => x.IsUsed).HasColumnName("is_used").HasDefaultValue(false);
        });
    }
}
